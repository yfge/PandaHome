"""P2P credentials are downloadable only by active administrators."""

import tomllib
from contextlib import nullcontext
from unittest.mock import AsyncMock

import pytest

from src.app.auth.auth import create_access_token
from src.app.database.database import get_db
from src.app.main import app
from src.app.models.p2p_service import P2PService
from src.app.routers.p2p import get_p2p_manager
from src.app.services.p2p import P2PConfig, P2PManager


DRAFT = {"name": "Home photos", "local_ip": "127.0.0.1", "local_port": 8080}


def headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.username})}"}


@pytest.fixture
def manager(db_session, tmp_path):
    value = P2PManager(P2PConfig(
        state_dir=tmp_path, server_addr="frps.example.test", token="server-auth-private",
        tls_trusted_ca_file=str(tmp_path / "ca.crt"),
    ), lambda: nullcontext(db_session))
    value.reconcile = AsyncMock()
    original_db = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_p2p_manager] = lambda: value
    yield value
    app.dependency_overrides.pop(get_p2p_manager, None)
    app.dependency_overrides[get_db] = original_db


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/p2p"), ("POST", "/api/p2p/services"),
    ("PUT", "/api/p2p/services/1"), ("DELETE", "/api/p2p/services/1"),
    ("POST", "/api/p2p/services/1/rotate-key"),
    ("GET", "/api/p2p/services/1/visitor"), ("GET", "/api/p2p/ca"),
    ("POST", "/api/p2p/reconcile"),
])
def test_every_endpoint_requires_active_admin(client, manager, normal_user, admin_user, db_session, method, path):
    assert client.request(method, path, json=DRAFT).status_code == 401
    assert client.request(method, path, json=DRAFT, headers=headers(normal_user)).status_code == 403
    admin_user.is_active = False
    db_session.commit()
    assert client.request(method, path, json=DRAFT, headers=headers(admin_user)).status_code == 403
    manager.reconcile.assert_not_awaited()


def test_crud_keeps_credentials_out_of_status(client, manager, admin_user, db_session):
    auth = headers(admin_user)
    created = client.post("/api/p2p/services", json=DRAFT, headers=auth)
    assert created.status_code == 201, created.text
    view = created.json()["data"]
    row = db_session.get(P2PService, view["id"])
    assert len(row.uid) == 32 and len(row.secret_key) >= 32
    secret, uid = row.secret_key, row.uid
    assert "secret_key" not in created.text and secret not in created.text
    state = client.get("/api/p2p", headers=auth)
    assert state.json()["data"]["provider"]["connection_type"] == "unknown"
    assert secret not in state.text and manager.config.token not in state.text
    edited = client.put(f"/api/p2p/services/{row.id}", json={**DRAFT, "enabled": False}, headers=auth)
    assert edited.json()["data"]["status"] == "disabled"
    db_session.refresh(row)
    assert row.secret_key == secret and row.uid == uid
    assert client.get(f"/api/p2p/services/{row.id}/visitor", headers=auth).status_code == 409
    assert client.delete(f"/api/p2p/services/{row.id}", headers=auth).status_code == 200
    assert db_session.query(P2PService).count() == 0
    assert manager.reconcile.await_count == 3


def test_download_is_credential_bearing_loopback_only_and_not_cached(client, manager, admin_user, db_session):
    auth = headers(admin_user)
    value = client.post("/api/p2p/services", json=DRAFT, headers=auth).json()["data"]
    row = db_session.get(P2PService, value["id"])
    download = client.get(f"/api/p2p/services/{row.id}/visitor?bind_port=18888", headers=auth)
    assert download.status_code == 200
    assert download.headers["cache-control"] == "no-store"
    assert "attachment" in download.headers["content-disposition"]
    config = tomllib.loads(download.text)
    assert config["auth"]["token"] == manager.config.token
    assert config["transport"]["tls"]["trustedCaFile"] == "frps-ca.crt"
    assert {item["bindAddr"] for item in config["visitors"]} == {"127.0.0.1"}
    xtcp = next(item for item in config["visitors"] if item["type"] == "xtcp")
    assert xtcp["secretKey"] == row.secret_key and xtcp["bindPort"] == 18888
    assert client.get(f"/api/p2p/services/{row.id}/visitor?bind_port=0", headers=auth).status_code == 422


def test_rotated_key_invalidates_old_visitor_config(client, manager, admin_user, db_session):
    auth = headers(admin_user)
    value = client.post("/api/p2p/services", json=DRAFT, headers=auth).json()["data"]
    row = db_session.get(P2PService, value["id"])
    secret, uid = row.secret_key, row.uid
    response = client.post(f"/api/p2p/services/{row.id}/rotate-key", headers=auth)
    assert response.status_code == 200
    db_session.refresh(row)
    assert row.secret_key != secret and row.uid == uid
    download = client.get(f"/api/p2p/services/{row.id}/visitor", headers=auth)
    assert secret not in download.text and row.secret_key in download.text
    assert row.secret_key not in response.text
    assert manager.reconcile.await_count == 2


@pytest.mark.parametrize("bad", [
    {"local_ip": "0.0.0.0"}, {"local_ip": "224.0.0.1"}, {"local_ip": "::1"},
    {"local_port": 0}, {"protocol": "UDP"}, {"secret_key": "user-controlled"}, {"name": " "},
])
def test_invalid_or_extra_fields_do_not_create_exposure(client, manager, admin_user, db_session, bad):
    response = client.post("/api/p2p/services", json={**DRAFT, **bad}, headers=headers(admin_user))
    assert response.status_code == 422
    assert db_session.query(P2PService).count() == 0
    manager.reconcile.assert_not_awaited()


def test_ca_download_rejects_private_keys_and_missing_certificates(client, manager, admin_user, tmp_path):
    auth = headers(admin_user)
    assert client.get("/api/p2p/ca", headers=auth).status_code == 409
    ca = tmp_path / "ca.crt"
    ca.write_text("-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----")
    response = client.get("/api/p2p/ca", headers=auth)
    assert response.status_code == 409 and "secret" not in response.text
    ca.write_text("-----BEGIN CERTIFICATE-----\nPUBLIC\n-----END CERTIFICATE-----\n")
    response = client.get("/api/p2p/ca", headers=auth)
    assert response.status_code == 200 and response.text == ca.read_text()
    assert response.headers["cache-control"] == "no-store"


def test_missing_services_are_not_found(client, manager, admin_user):
    auth = headers(admin_user)
    assert client.get("/api/p2p/services/999/visitor", headers=auth).status_code == 404
    assert client.put("/api/p2p/services/999", json=DRAFT, headers=auth).status_code == 404
    assert client.delete("/api/p2p/services/999", headers=auth).status_code == 404
    assert client.post("/api/p2p/services/999/rotate-key", headers=auth).status_code == 404


def test_retry_only_reports_local_provider_facts(client, manager, admin_user):
    response = client.post("/api/p2p/reconcile", headers=headers(admin_user))
    assert response.status_code == 200
    assert response.json()["data"]["connection_type"] == "unknown"
    manager.reconcile.assert_awaited_once()
