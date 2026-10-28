import asyncio
import os
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.app.services.relay as relay_module
from src.app.models.p2p_service import P2PService
from src.app.schemas.p2p import P2PServiceConfig
from src.app.services.p2p import P2PConfig, P2PManager


class FakeProcess:
    def __init__(self):
        self.returncode = None
        self.terminated = False
        self.exited = asyncio.Event()

    def terminate(self):
        self.terminated = True
        self.returncode = -15
        self.exited.set()

    def kill(self):
        self.returncode = -9
        self.exited.set()

    async def wait(self):
        await self.exited.wait()
        return self.returncode


@pytest.fixture
def sessions(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'p2p.db'}")
    P2PService.__table__.create(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


def add_service(sessions, **fields):
    values = {"name": "NAS", "local_ip": "127.0.0.1", "local_port": 5000}
    values.update(fields)
    with sessions() as db:
        row = P2PService(**values)
        db.add(row)
        db.commit()
        return row


@pytest.fixture
def spawns(monkeypatch):
    monkeypatch.setattr(relay_module.shutil, "which", lambda binary: "/usr/local/bin/frpc")
    calls = []

    async def spawn(*args, **kwargs):
        process = FakeProcess()
        calls.append((args, kwargs, process))
        return process

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", spawn)
    return calls


@pytest_asyncio.fixture
async def manager(tmp_path, sessions, spawns):
    manager = P2PManager(P2PConfig(
        state_dir=tmp_path / "state", server_addr="relay.example.com", token="server-token",
        stun_server="stun.example.com:3478", fallback_timeout_ms=1500,
    ), sessions)
    yield manager
    await manager.shutdown()


@pytest.mark.asyncio
async def test_provider_and_visitor_names_credentials_encryption_and_fallback_match(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()

    provider = tomllib.loads(manager.relay._config_path.read_text())
    visitor = tomllib.loads(manager.render_visitor(row, bind_port=18081))
    assert provider["serverAddr"] == visitor["serverAddr"] == "relay.example.com"
    assert provider["natHoleStunServer"] == visitor["natHoleStunServer"] == "stun.example.com:3478"
    assert provider["auth"]["token"] == visitor["auth"]["token"] == "server-token"
    assert provider["transport"]["tls"]["enable"] is True
    assert visitor["transport"]["tls"]["enable"] is True
    by_name = {entry["name"]: entry for entry in provider["proxies"]}
    for entry in visitor["visitors"]:
        counterpart = by_name[entry["serverName"]]
        assert counterpart["secretKey"] == entry["secretKey"] == row.secret_key
        assert counterpart["transport"]["useEncryption"] is True
        assert entry["transport"]["useEncryption"] is True
        assert counterpart["localIP"] == "127.0.0.1"
        assert counterpart["localPort"] == 5000
        assert "remotePort" not in counterpart
        assert entry["bindAddr"] == "127.0.0.1"
    stcp, xtcp = visitor["visitors"]
    assert stcp["type"] == "stcp" and stcp["bindPort"] == -1
    assert xtcp["type"] == "xtcp" and xtcp["bindPort"] == 18081
    assert xtcp["fallbackTo"] == stcp["name"]
    assert xtcp["fallbackTimeoutMs"] == 1500
    assert xtcp["keepTunnelOpen"] is True
    assert "p2p" in manager.relay._config_path.parts
    assert "server-token" not in repr(spawns[0][0])


@pytest.mark.asyncio
async def test_provider_command_is_parent_guarded_without_credential_arguments(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()
    command = spawns[0][0]
    assert command[0] == sys.executable
    assert Path(command[1]).is_absolute() and Path(command[1]).name == "process_guard.py"
    assert command[2:5] == ("--parent", str(os.getpid()), "--parent-created-at")
    assert float(command[5]) > 0
    assert command[6] == "--"
    assert command[7:] == (str(Path("/usr/local/bin/frpc").resolve()), "-c", str(manager.relay._config_path))
    assert manager.config.token not in repr(command)
    assert row.secret_key not in repr(command)


@pytest.mark.asyncio
async def test_fallback_can_be_disabled_for_both_ends(manager, sessions):
    row = add_service(sessions, fallback_enabled=False)
    await manager.reconcile()
    provider = tomllib.loads(manager.relay._config_path.read_text())
    visitor = tomllib.loads(manager.render_visitor(row))
    assert [entry["type"] for entry in provider["proxies"]] == ["xtcp"]
    assert [entry["type"] for entry in visitor["visitors"]] == ["xtcp"]
    assert "fallbackTo" not in visitor["visitors"][0]


@pytest.mark.asyncio
async def test_disable_and_removal_stop_existing_provider(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()
    with sessions() as db:
        persisted = db.get(P2PService, row.id)
        persisted.enabled = False
        db.commit()
    await manager.reconcile()
    assert spawns[0][2].terminated is True
    assert manager.status()["running"] is False
    assert not manager.relay._config_path.exists()
    with pytest.raises(ValueError, match="Enable"):
        manager.render_visitor(persisted)
    assert manager.service_view(persisted).status == "disabled"
    with sessions() as db:
        db.get(P2PService, row.id).enabled = True
        db.commit()
    await manager.reconcile()
    with sessions() as db:
        db.delete(db.get(P2PService, row.id))
        db.commit()
    await manager.reconcile()
    assert spawns[-1][2].terminated is True
    assert not manager.relay._config_path.exists()


@pytest.mark.asyncio
async def test_persisted_uid_secret_and_restart_reconcile_are_stable(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()
    rendered = manager.relay._config_path.read_text()
    await manager.shutdown()
    restarted = P2PManager(manager.config, sessions)
    try:
        await restarted.reconcile()
        assert restarted.relay._config_path.read_text() == rendered
        with sessions() as db:
            persisted = db.get(P2PService, row.id)
            assert persisted.uid == row.uid
            assert persisted.secret_key == row.secret_key
        await restarted.reconcile()
        assert len(spawns) == 2
    finally:
        await restarted.shutdown()


def test_uids_and_keys_are_generated_independently_and_never_serialized(manager, sessions):
    first, second = add_service(sessions), add_service(sessions)
    assert first.uid != second.uid and len(first.uid) == 32
    assert first.secret_key != second.secret_key and len(first.secret_key) >= 43
    view = manager.service_view(first).model_dump()
    assert "uid" not in view and "secret_key" not in view
    assert first.secret_key not in repr(first)
    assert "server-token" not in repr(manager.config)
    assert first.secret_key not in repr(manager.status())


@pytest.mark.asyncio
async def test_special_credentials_round_trip_without_go_template_expansion(manager, sessions):
    key = 'private"\\\n\x7f{{ .Envs.NOT_A_REAL_SECRET }}'
    token = 'token"\\\n{{ .Envs.NOT_A_REAL_TOKEN }}'
    row = add_service(sessions, secret_key=key)
    escaped = P2PManager(replace(manager.config, token=token), sessions)
    try:
        await escaped.reconcile()
        provider_text = escaped.relay._config_path.read_text()
        visitor_text = escaped.render_visitor(row)
        assert "{{" not in provider_text and "{{" not in visitor_text
        assert tomllib.loads(provider_text)["auth"]["token"] == token
        assert tomllib.loads(visitor_text)["auth"]["token"] == token
        assert tomllib.loads(provider_text)["proxies"][0]["secretKey"] == key
        assert tomllib.loads(visitor_text)["visitors"][0]["secretKey"] == key
    finally:
        await escaped.shutdown()


@pytest.mark.asyncio
async def test_running_provider_never_claims_peer_or_direct_success(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()
    assert manager.status()["running"] is True
    assert manager.status()["connection_type"] == "unknown"
    view = manager.service_view(row)
    assert view.status == "awaiting_connection"
    assert view.reason_code == "p2p_awaiting_connection"
    assert view.connection_type == "unknown"
    spawns[-1][2].returncode = 1
    assert manager.status()["reason_code"] == "p2p_process_exited"
    assert manager.service_view(row).status == "error"
    await manager.reconcile()
    assert len(spawns) == 2
    assert manager.service_view(row).connection_type == "unknown"


@pytest.mark.asyncio
async def test_config_and_key_change_reap_old_provider(manager, sessions, spawns):
    row = add_service(sessions)
    await manager.reconcile()
    with sessions() as db:
        persisted = db.get(P2PService, row.id)
        persisted.secret_key = "rotated-service-key"
        persisted.local_port = 5001
        db.commit()
    await manager.reconcile()
    assert spawns[0][2].terminated is True
    assert len(spawns) == 2
    rendered = tomllib.loads(manager.relay._config_path.read_text())
    assert rendered["proxies"][0]["secretKey"] == "rotated-service-key"
    assert rendered["proxies"][0]["localPort"] == 5001


@pytest.mark.asyncio
async def test_background_retries_spawn_failure_without_leaking_message(manager, sessions, monkeypatch, caplog):
    row = add_service(sessions)
    attempts = 0
    succeeded = asyncio.Event()

    async def flaky_spawn(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("server-token should never be logged")
        succeeded.set()
        return FakeProcess()

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", flaky_spawn)
    retry = P2PManager(replace(manager.config, retry_interval_seconds=0.01), sessions)
    try:
        await retry.startup()
        assert retry.status()["reason_code"] == "p2p_start_failed"
        assert retry.service_view(row).status == "error"
        assert "server-token" not in caplog.text
        await asyncio.wait_for(succeeded.wait(), timeout=1)
        # Completion of process creation occurs after the fake signals its event.
        for _ in range(10):
            if retry.status()["running"]:
                break
            await asyncio.sleep(0)
        assert retry.status()["running"] is True
        assert retry.status()["reason_code"] is None
        assert retry.service_view(row).status == "awaiting_connection"
    finally:
        await retry.shutdown()
    assert retry._task is None
    assert retry.status()["running"] is False


@pytest.mark.asyncio
async def test_database_error_is_sanitized_and_next_reconcile_recovers(manager, sessions):
    add_service(sessions)
    await manager.reconcile()
    working_factory = manager.session_factory

    def unavailable_database():
        raise RuntimeError("private database connection value")

    manager.session_factory = unavailable_database
    await manager.reconcile()
    assert manager.status()["reason_code"] == "p2p_reconcile_failed"
    assert manager.status()["running"] is False
    manager.session_factory = working_factory
    await manager.reconcile()
    assert manager.status()["running"] is True


@pytest.mark.asyncio
async def test_unconfigured_and_missing_binary_are_setup_states(manager, sessions, monkeypatch):
    row = add_service(sessions)
    blank = P2PManager(replace(manager.config, server_addr=""), sessions)
    await blank.reconcile()
    assert blank.service_view(row).status == "needs_setup"
    assert blank.status()["reason_code"] == "p2p_not_configured"
    with pytest.raises(ValueError, match="Configure"):
        blank.render_visitor(row)
    monkeypatch.setattr(relay_module.shutil, "which", lambda binary: None)
    await manager.reconcile()
    assert manager.service_view(row).status == "needs_setup"
    assert manager.status()["reason_code"] == "p2p_binary_missing"


@pytest.mark.asyncio
async def test_trusted_ca_is_local_for_provider_and_portable_for_visitor(manager, sessions):
    row = add_service(sessions)
    secured = P2PManager(replace(
        manager.config, tls_trusted_ca_file="/private/provider/frps.crt", tls_server_name="frps.example.com",
    ), sessions)
    try:
        await secured.reconcile()
        provider_tls = tomllib.loads(secured.relay._config_path.read_text())["transport"]["tls"]
        visitor_tls = tomllib.loads(secured.render_visitor(row))["transport"]["tls"]
        assert provider_tls["trustedCaFile"] == "/private/provider/frps.crt"
        assert visitor_tls["trustedCaFile"] == "frps-ca.crt"
        assert provider_tls["serverName"] == visitor_tls["serverName"] == "frps.example.com"
        assert secured.status()["ca_required"] is True
        assert "/private/provider" not in repr(secured.status())
    finally:
        await secured.shutdown()


@pytest.mark.parametrize("port", [0, -1, 65536, True, 1.5, "18080"])
def test_visitor_cannot_bind_invalid_port(manager, sessions, port):
    with pytest.raises(ValueError, match="port"):
        manager.render_visitor(add_service(sessions), bind_port=port)


@pytest.mark.parametrize("ip", ["0.0.0.0", "224.0.0.1", "255.255.255.255", "::1", "not-an-ip"])
def test_schema_rejects_non_unicast_ipv4_and_udp_fields(ip):
    with pytest.raises(ValidationError):
        P2PServiceConfig(name="NAS", local_ip=ip, local_port=5000)
    with pytest.raises(ValidationError):
        P2PServiceConfig(name="NAS", local_ip="127.0.0.1", local_port=5000, protocol="UDP")


@pytest.mark.parametrize("fields", [
    {"server_port": 0}, {"fallback_timeout_ms": 0}, {"fallback_timeout_ms": 1.5},
    {"retry_interval_seconds": 0}, {"retry_interval_seconds": 301},
])
def test_config_rejects_unbounded_timing_or_ports(tmp_path, fields):
    with pytest.raises(ValueError):
        P2PConfig(state_dir=tmp_path, **fields)


def test_ca_paths_resolve_before_native_client_changes_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative = P2PConfig(state_dir=tmp_path, tls_trusted_ca_file=" ca.crt ")
    assert relative.tls_trusted_ca_file == str(tmp_path / "ca.crt")
    home = P2PConfig(state_dir=tmp_path, tls_trusted_ca_file="~/frps-ca.crt")
    assert home.tls_trusted_ca_file == str(Path.home() / "frps-ca.crt")
