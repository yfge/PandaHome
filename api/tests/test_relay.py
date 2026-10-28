import asyncio
import json
import os
import signal
import socket
import stat
import sys
import tomllib
from contextlib import suppress
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import psutil

import src.app.services.relay as relay_module
from src.app.services.relay import FrpRelay, RelayConfig, RelayError, RelayMapping


class FakeProcess:
    def __init__(self, *, ignores_terminate=False):
        self.returncode = None
        self.terminated = 0
        self.killed = 0
        self.ignores_terminate = ignores_terminate
        self.exited = asyncio.Event()

    def terminate(self):
        self.terminated += 1
        if not self.ignores_terminate:
            self.exit(-15)

    def kill(self):
        self.killed += 1
        self.exit(-9)

    def exit(self, code):
        self.returncode = code
        self.exited.set()

    async def wait(self):
        await self.exited.wait()
        return self.returncode


@pytest.fixture
def relay(tmp_path, monkeypatch):
    monkeypatch.setattr(relay_module.shutil, "which", lambda binary: "/usr/local/bin/frpc")
    return FrpRelay(
        RelayConfig(
            state_dir=tmp_path,
            server_addr="relay.example.com",
            public_host="public.example.com",
            token="private-token",
        )
    )


@pytest.fixture
def spawns(monkeypatch):
    calls = []

    async def spawn(*args, **kwargs):
        process = FakeProcess()
        calls.append((args, kwargs, process))
        return process

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", spawn)
    return calls


def mapping(service_id=1, *, public_port=18080, protocol="TCP"):
    return RelayMapping(service_id, "192.168.1.50", 8080, public_port, protocol)


@pytest.mark.asyncio
async def test_native_config_and_safe_process_arguments(relay, spawns, tmp_path):
    await relay.apply([mapping(), mapping(2, public_port=15353, protocol="UDP")])
    config_path = tmp_path / "frp" / "frpc.toml"
    data = tomllib.loads(config_path.read_text())
    assert data["serverAddr"] == "relay.example.com"
    assert data["serverPort"] == 7000
    assert data["loginFailExit"] is False
    assert data["transport"]["tls"]["enable"] is True
    assert data["auth"] == {"method": "token", "token": "private-token"}
    assert data["webServer"]["addr"] == "127.0.0.1"
    assert 1 <= data["webServer"]["port"] <= 65535
    assert data["webServer"]["user"] == "pandahome"
    assert len(data["webServer"]["password"]) >= 32
    assert data["webServer"]["password"] not in str(relay.status())
    assert data["proxies"] == [
        {"name": "pandahome-1-tcp", "type": "tcp", "localIP": "192.168.1.50", "localPort": 8080, "remotePort": 18080},
        {"name": "pandahome-2-udp", "type": "udp", "localIP": "192.168.1.50", "localPort": 8080, "remotePort": 15353},
    ]
    args, kwargs, _ = spawns[0]
    assert args[0] == sys.executable
    assert Path(args[1]).is_absolute() and Path(args[1]).name == "process_guard.py"
    assert args[2:5] == ("--parent", str(os.getpid()), "--parent-created-at")
    assert float(args[5]) > 0
    assert args[6:] == ("--", "/usr/local/bin/frpc", "-c", str(config_path))
    assert "private-token" not in str(args)
    assert kwargs == {
        "stdin": asyncio.subprocess.DEVNULL,
        "stdout": asyncio.subprocess.DEVNULL,
        "stderr": asyncio.subprocess.DEVNULL,
        "cwd": str(tmp_path / "frp"),
    }
    assert stat.S_IMODE((tmp_path / "frp").stat().st_mode) == 0o700
    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
    assert relay.status() == {
        "configured": True,
        "available": True,
        "running": True,
        "public_host": "public.example.com",
        "reason_code": None,
    }
    await relay.stop()


@pytest.mark.asyncio
async def test_unchanged_order_is_noop_and_change_stops_old_child(relay, spawns):
    first, second = mapping(), mapping(2, public_port=18081)
    await relay.apply([second, first])
    await relay.apply([first, second])
    assert len(spawns) == 1
    assert spawns[0][2].terminated == 0
    await relay.apply([mapping(public_port=19090)])
    assert len(spawns) == 2
    assert spawns[0][2].returncode == -15
    assert spawns[0][2].terminated == 1
    await relay.stop()


@pytest.mark.asyncio
async def test_dead_process_is_not_healthy_and_restarts(relay, spawns):
    await relay.apply([mapping()])
    spawns[0][2].exit(1)
    assert relay.status()["running"] is False
    assert relay.status()["reason_code"] == "relay_process_exited"
    await relay.apply([mapping()])
    assert len(spawns) == 2
    assert relay.status()["running"] is True
    await relay.stop()


@pytest.mark.asyncio
async def test_native_registration_uses_only_current_owned_proxy_names(relay, spawns):
    read = AsyncMock(return_value={1: True, 2: False})
    relay._status_client.registration = read
    assert await relay.registration() == {}
    await relay.apply([mapping(), mapping(2, public_port=15353, protocol="UDP")])
    assert await relay.registration() == {1: True, 2: False}
    read.assert_awaited_once_with({"pandahome-1-tcp": 1, "pandahome-2-udp": 2})
    spawns[0][2].exit(1)
    assert await relay.registration() == {}
    await relay.stop()


@pytest.mark.asyncio
async def test_process_exit_during_registration_cannot_claim_acceptance(relay, spawns):
    await relay.apply([mapping()])

    async def exited_while_reading(expected):
        spawns[0][2].exit(1)
        return {1: True}

    relay._status_client.registration = exited_while_reading
    assert await relay.registration() == {1: False}
    await relay.stop()


@pytest.mark.asyncio
async def test_failed_reconfiguration_cannot_reuse_old_registration_evidence(relay, spawns, monkeypatch):
    await relay.apply([mapping()])
    read = AsyncMock(return_value={1: True})
    relay._status_client.registration = read
    assert await relay.registration() == {1: True}
    with monkeypatch.context() as changes:
        changes.setattr(relay, "_terminate", AsyncMock(side_effect=RelayError("Unable to stop the relay client")))
        with pytest.raises(RelayError):
            await relay.apply([mapping(public_port=19090)])
    assert spawns[0][2].returncode is None
    assert await relay.registration() == {}
    assert read.await_count == 1
    await relay.stop()


@pytest.mark.asyncio
async def test_stop_is_idempotent_and_does_not_remove_other_state(relay, spawns, tmp_path):
    await relay.apply([mapping()])
    unrelated = tmp_path / "frp" / "keep.txt"
    unrelated.write_text("owned by somebody else")
    await relay.stop()
    await relay.stop()
    assert spawns[0][2].terminated == 1
    assert not (tmp_path / "frp" / "frpc.toml").exists()
    assert unrelated.read_text() == "owned by somebody else"
    assert relay.status()["reason_code"] == "relay_stopped"


@pytest.mark.asyncio
async def test_empty_desired_set_removes_all_forwarding(relay, spawns, tmp_path):
    await relay.apply([mapping()])
    await relay.apply([])
    assert spawns[0][2].returncode == -15
    assert not (tmp_path / "frp" / "frpc.toml").exists()
    assert relay.status()["running"] is False


@pytest.mark.asyncio
async def test_missing_server_and_binary_are_explicit(tmp_path, monkeypatch, spawns):
    monkeypatch.setattr(relay_module.shutil, "which", lambda binary: None)
    relay = FrpRelay(RelayConfig(state_dir=tmp_path))
    await relay.apply([mapping()])
    assert relay.status()["reason_code"] == "relay_not_configured"
    assert relay.status()["configured"] is False
    assert relay.status()["available"] is False
    assert relay.status()["public_host"] is None
    relay = FrpRelay(RelayConfig(state_dir=tmp_path, server_addr="relay.example.com"))
    await relay.apply([mapping()])
    assert relay.status()["reason_code"] == "relay_binary_missing"
    assert relay.status()["public_host"] == "relay.example.com"
    assert not spawns


@pytest.mark.asyncio
async def test_start_failure_does_not_leak_secret(relay, monkeypatch, tmp_path):
    async def fail(*args, **kwargs):
        raise OSError("private-token should never appear")

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", fail)
    with pytest.raises(RelayError, match="Unable to start") as error:
        await relay.apply([mapping()])
    assert "private-token" not in str(error.value)
    assert "private-token" not in repr(relay.config)
    assert relay.status()["reason_code"] == "relay_start_failed"
    assert not (tmp_path / "frp" / "frpc.toml").exists()


@pytest.mark.asyncio
async def test_termination_timeout_escalates_before_restart(relay, spawns):
    relay._STOP_TIMEOUT = 0.01
    await relay.apply([mapping()])
    old = spawns[0][2]
    old.ignores_terminate = True
    await relay.apply([mapping(public_port=19090)])
    assert old.terminated == 1
    assert old.killed == 1
    assert old.returncode == -9
    assert len(spawns) == 2
    await relay.stop()


@pytest.mark.asyncio
async def test_cancellation_during_spawn_reaps_new_child(relay, monkeypatch, tmp_path):
    started, release = asyncio.Event(), asyncio.Event()
    process = FakeProcess()

    async def delayed_spawn(*args, **kwargs):
        started.set()
        await release.wait()
        return process

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", delayed_spawn)
    task = asyncio.create_task(relay.apply([mapping()]))
    await started.wait()
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.returncode == -15
    assert not (tmp_path / "frp" / "frpc.toml").exists()


@pytest.mark.asyncio
async def test_toml_strings_roundtrip_without_template_expansion(tmp_path, monkeypatch, spawns):
    token = 'quotes"\\newline\n\t\x00\x7f 汉字🐼 {{ .Envs.SECRET }}'
    monkeypatch.setattr(relay_module.shutil, "which", lambda binary: "/usr/local/bin/frpc")
    relay = FrpRelay(RelayConfig(state_dir=tmp_path, server_addr="relay.example.com", token=token))
    await relay.apply([RelayMapping(1, 'lan"\\host\n', 80, 8080, "TCP")])
    raw = (tmp_path / "frp" / "frpc.toml").read_text()
    assert "{{" not in raw
    assert tomllib.loads(raw)["auth"]["token"] == token
    assert tomllib.loads(raw)["proxies"][0]["localIP"] == 'lan"\\host\n'
    await relay.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mappings",
    [
        [mapping(protocol="HTTP")],
        [mapping(public_port=0)],
        [mapping(public_port=65536)],
        [mapping(), mapping()],
        [mapping(), mapping(2)],
        [RelayMapping(0, "127.0.0.1", 80, 8080, "TCP")],
    ],
)
async def test_invalid_mapping_rejected_without_start(relay, spawns, mappings):
    with pytest.raises(ValueError):
        await relay.apply(mappings)
    assert not spawns


def test_state_inside_checkout_is_rejected(tmp_path, monkeypatch):
    repository = tmp_path / "checkout"
    (repository / ".git").mkdir(parents=True)
    source = repository / "api" / "src" / "app" / "services" / "relay.py"
    source.parent.mkdir(parents=True)
    source.touch()
    monkeypatch.setattr(relay_module, "__file__", str(source))
    with pytest.raises(RelayError, match="outside the source checkout"):
        FrpRelay(RelayConfig(state_dir=repository / ".relay"))


@pytest.mark.asyncio
async def test_symlink_directory_is_rejected_without_touching_target(relay, spawns, tmp_path):
    target = tmp_path / "other"
    target.mkdir(mode=0o755)
    (tmp_path / "frp").symlink_to(target, target_is_directory=True)
    with pytest.raises(RelayError, match="private relay configuration"):
        await relay.apply([mapping()])
    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert not spawns


@pytest.mark.asyncio
@pytest.mark.skipif(os.name != "posix", reason="Backend SIGKILL regression exercises the POSIX deployment lifecycle")
async def test_default_public_relay_reclaims_same_port_after_backend_sigkill(tmp_path):
    payload, owner_script, ready = tmp_path / "native.py", tmp_path / "backend.py", tmp_path / "native-ready.json"
    payload.write_text(
        f"#!{sys.executable}\n"
        "import json, os, socket, sys, tomllib\nfrom pathlib import Path\nimport psutil\n"
        "proxy = tomllib.loads(Path(sys.argv[2]).read_text())['proxies'][0]\n"
        "with socket.socket() as listener:\n"
        "    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
        "    listener.bind(('127.0.0.1', proxy['remotePort']))\n    listener.listen()\n"
        "    Path(os.environ['PANDAHOME_NATIVE_READY']).write_text(json.dumps({\n"
        "        'pid': os.getpid(), 'created_at': psutil.Process().create_time(),\n"
        "        'port': listener.getsockname()[1], 'name': proxy['name'],\n    }))\n"
        "    while True:\n        connection, _ = listener.accept()\n"
        "        with connection:\n            while data := connection.recv(128):\n                connection.sendall(data)\n"
    )
    payload.chmod(0o700)
    owner_script.write_text(
        "import asyncio, sys\nfrom pathlib import Path\n"
        "from src.app.services.relay import FrpRelay, RelayConfig, RelayMapping\n"
        "async def main():\n"
        "    relay = FrpRelay(RelayConfig(state_dir=Path(sys.argv[1]), binary=sys.argv[2], server_addr='unused'))\n"
        "    await relay.apply([RelayMapping(1, '127.0.0.1', 8080, int(sys.argv[3]), 'TCP')])\n"
        "    try:\n        await asyncio.Event().wait()\n"
        "    finally:\n        await relay.stop()\n"
        "asyncio.run(main())\n"
    )
    environment = {
        **os.environ,
        "PANDAHOME_NATIVE_READY": str(ready),
        "PYTHONPATH": str(Path(relay_module.__file__).resolve().parents[3]),
    }
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        public_port = reservation.getsockname()[1]
    previous_identity = None
    for _generation in range(2):
        ready.unlink(missing_ok=True)
        owner = await asyncio.create_subprocess_exec(
            sys.executable, str(owner_script), str(tmp_path / "state"), str(payload), str(public_port),
            env=environment, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        descendants = []
        try:
            data = await _wait_native_listener(ready, owner)
            descendants = psutil.Process(owner.pid).children(recursive=True)
            assert data["pid"] in {child.pid for child in descendants}
            assert (data["port"], data["name"]) == (public_port, "pandahome-1-tcp")
            identity = data["pid"], data["created_at"]
            assert identity != previous_identity
            previous_identity = identity
            await _native_roundtrip(public_port)
            owner.kill()
            assert await asyncio.wait_for(owner.wait(), 2) == -signal.SIGKILL
            await _wait_owned_processes_stopped(descendants)
            # A hard-killed backend cannot remove config; its replacement must
            # reuse this state directory and the same proxy name/public port.
            assert (tmp_path / "state" / "frp" / "frpc.toml").exists()
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", public_port), 1)
            except (OSError, TimeoutError):
                pass
            else:
                writer.close()
                await writer.wait_closed()
                pytest.fail("Native listener survived backend SIGKILL")
        finally:
            if owner.returncode is None:
                with suppress(psutil.NoSuchProcess):
                    descendants.extend(psutil.Process(owner.pid).children(recursive=True))
                owner.kill()
                await asyncio.wait_for(owner.wait(), 2)
            for child in reversed(descendants):
                with suppress(psutil.NoSuchProcess):
                    child.kill()
            await _wait_owned_processes_stopped(descendants)


async def _wait_native_listener(ready, owner):
    deadline = asyncio.get_running_loop().time() + 8
    while asyncio.get_running_loop().time() < deadline:
        try:
            return json.loads(ready.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            assert owner.returncode is None, "Backend exited before guarded native listener was ready"
            await asyncio.sleep(0.02)
    pytest.fail("Default public relay did not launch its native payload")


async def _native_roundtrip(port):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        payload = b"backend-death-proof"
        writer.write(payload)
        await writer.drain()
        assert await asyncio.wait_for(reader.readexactly(len(payload)), 1) == payload
    finally:
        writer.close()
        await writer.wait_closed()


async def _wait_owned_processes_stopped(processes):
    deadline = asyncio.get_running_loop().time() + 5
    while asyncio.get_running_loop().time() < deadline:
        live = []
        for process in processes:
            with suppress(psutil.NoSuchProcess):
                if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    live.append(process)
        if not live:
            return
        await asyncio.sleep(0.02)
    pytest.fail("Backend death left an owned relay process alive")
