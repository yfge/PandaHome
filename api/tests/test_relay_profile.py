"""Private relay settings, safe admin responses and original controller wiring."""

import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from src.app.auth.auth import create_access_token
from src.app.config import settings
from src.app.main import app
from src.app.routers.access import get_access_controller
from src.app.schemas.relay import RelayProfile
from src.app.services.access.controller import AccessController
from src.app.services.relay_profile import RelayProfileError, RelayProfileStore


def headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.username})}"}


@pytest.fixture
def managed_controller(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "RELAY_STATE_DIR", tmp_path)
    monkeypatch.setattr(settings, "RELAY_SERVER_ADDR", "relay.example.com")
    monkeypatch.setattr(settings, "RELAY_TOKEN", SecretStr("original private token"))
    controller = AccessController(SimpleNamespace(initialized=False))
    app.dependency_overrides[get_access_controller] = lambda: controller
    yield controller
    app.dependency_overrides.pop(get_access_controller, None)


def test_profile_requires_active_admin(client, managed_controller, normal_user, admin_user, db_session):
    assert client.get("/api/access/relay-config").status_code == 401
    assert client.put("/api/access/relay-config", json={}).status_code == 401
    for method in (client.get, client.put):
        assert method("/api/access/relay-config", headers=headers(normal_user)).status_code == 403
    auth = headers(admin_user)
    admin_user.is_active = False
    db_session.commit()
    assert client.get("/api/access/relay-config", headers=auth).status_code == 403


def test_admin_save_keeps_or_replaces_token_without_echo(client, managed_controller, admin_user, tmp_path):
    auth = headers(admin_user)
    endpoint = "/api/access/relay-config"
    view = client.get(endpoint, headers=auth).json()["data"]
    assert view["source"] == "environment" and view["has_token"] is True
    assert "token" not in view and "original private token" not in str(view)
    base = {"server_addr": "relay.example.com", "public_host": "public.example.com"}
    for addition, expected in (({}, "original private token"), ({"token": " new private token "}, " new private token "),
                               ({"token": None}, " new private token "), ({"clear_token": True}, ""),
                               ({"token": "replace again"}, "replace again"), ({"token": ""}, "")):
        response = client.put(endpoint, headers=auth, json={**base, **addition})
        assert response.status_code == 200, response.text
        assert response.json()["data"]["source"] == "managed"
        assert response.json()["data"]["has_token"] is bool(expected)
        assert "token" not in response.json()["data"]
        assert managed_controller.relay.config.token == expected
        assert json.loads((tmp_path / "relay-profile.json").read_text())["token"] == expected
    assert stat.S_IMODE((tmp_path / "relay-profile.json").stat().st_mode) == 0o600
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o700
    assert managed_controller.relay.status()["running"] is False
    # The original App/controller reloads the persisted profile on restart.
    restarted = AccessController(SimpleNamespace(initialized=False))
    assert restarted.relay.config.public_host == "public.example.com"
    assert restarted.relay.config.token == ""


@pytest.mark.parametrize("invalid", [
    {"ssh_enabled": True}, {"server_addr": "-oProxyCommand=evil"}, {"ssh_user": "root; echo bad"},
    {"server_port": 0}, {"public_host": "https://relay.example.com:8080/path"},
    {"tls_trusted_ca_file": "bad\npath"}, {"clear_token": True},
    {"binary": "frpc\x00bad"}, {"ssh_binary": "ssh\nbad"},
])
def test_invalid_request_never_echoes_new_credentials(client, managed_controller, admin_user, invalid):
    response = client.put("/api/access/relay-config", headers=headers(admin_user), json={
        "server_addr": "relay.example.com", "token": "new-secret-must-never-return", **invalid,
    })
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid relay configuration."}
    assert "new-secret" not in response.text


def test_malformed_managed_profile_never_falls_back_to_environment(tmp_path):
    store = RelayProfileStore(tmp_path, RelayProfile(server_addr="env.example.com"))
    path = tmp_path / "relay-profile.json"
    path.write_text('{"token":"do-not-echo", broken')
    path.chmod(0o600)
    with pytest.raises(RelayProfileError, match="Unable to read") as error:
        store.load()
    assert "do-not-echo" not in str(error.value)
    path.write_text('{}')
    path.chmod(0o644)
    with pytest.raises(RelayProfileError):
        store.load()


def test_profile_inside_checkout_is_rejected(tmp_path):
    import src.app.services.relay_profile as module
    checkout = next(parent for parent in Path(module.__file__).parents if (parent / ".git").exists())
    with pytest.raises(RelayProfileError, match="outside the source checkout"):
        RelayProfileStore(checkout / ".private-profile", RelayProfile())


@pytest.mark.asyncio
async def test_profile_change_stops_old_then_replaces_and_same_save_is_noop(managed_controller):
    controller = managed_controller
    old = controller.relay
    old.stop = AsyncMock()
    profile = RelayProfile(server_addr="changed.example.com", token=SecretStr("replacement"))
    await controller.save_relay_profile(profile)
    old.stop.assert_awaited_once()
    assert controller.reconciler.relay is controller.relay and controller.relay is not old
    new = controller.relay
    new.stop = AsyncMock()
    await controller.save_relay_profile(profile)
    assert controller.relay is new
    new.stop.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_failure_leaves_old_running_and_profile_unchanged(managed_controller, monkeypatch):
    controller = managed_controller
    old = controller.relay
    old.stop = AsyncMock()
    monkeypatch.setattr(os, "fsync", lambda *_: (_ for _ in ()).throw(OSError("secret path")))
    with pytest.raises(RelayProfileError):
        await controller.save_relay_profile(RelayProfile(server_addr="changed.example.com"))
    old.stop.assert_not_awaited()
    assert controller.relay is old
    assert controller.relay_profile()["source"] == "environment"


@pytest.mark.asyncio
async def test_final_rename_failure_retains_original_instance_and_wakes_retry(managed_controller, monkeypatch):
    controller = managed_controller
    old = controller.relay
    old.stop = AsyncMock()
    monkeypatch.setattr(os, "replace", lambda *_: (_ for _ in ()).throw(OSError("secret path")))
    with pytest.raises(RelayProfileError):
        await controller.save_relay_profile(RelayProfile(server_addr="changed.example.com"))
    old.stop.assert_awaited_once()
    assert controller.relay is old and controller._wake.is_set()
    assert controller.relay_profile()["source"] == "environment"


@pytest.mark.asyncio
async def test_stop_failure_cannot_commit_new_profile_or_discard_owned_instance(managed_controller):
    controller = managed_controller
    old = controller.relay
    old.stop = AsyncMock(side_effect=RuntimeError("native stop failed"))
    with pytest.raises(RuntimeError):
        await controller.save_relay_profile(RelayProfile(server_addr="changed.example.com"))
    assert controller.relay is old
    assert controller.relay_profile()["source"] == "environment"


def test_default_controller_carries_tls_and_ssh_settings(managed_controller, tmp_path, monkeypatch):
    values = {
        "TLS_TRUSTED_CA_FILE": str(tmp_path / "ca.pem"), "TLS_SERVER_NAME": "relay.example.com",
        "SSH_ENABLED": True, "SSH_HOST": "ssh.example.com", "SSH_USER": "root",
        "SSH_IDENTITY_FILE": str(tmp_path / "identity"), "SSH_KNOWN_HOSTS_FILE": str(tmp_path / "hosts"),
        "SERVER_ADDR": "127.0.0.1", "SERVER_PORT": 58354, "PUBLIC_HOST": "public.example.com",
    }
    for name, value in values.items():
        monkeypatch.setattr(settings, f"RELAY_{name}", value)
    config = AccessController(SimpleNamespace(initialized=False)).relay.config
    assert config.tls_trusted_ca_file == str(tmp_path / "ca.pem")
    assert config.tls_server_name == "relay.example.com"
    assert config.ssh.host == "ssh.example.com"
    assert (config.server_addr, config.server_port) == ("127.0.0.1", 58354)
