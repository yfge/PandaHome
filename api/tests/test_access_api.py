"""Public exposure changes must be authorized, persistent and cleanup-aware."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.app.auth.auth import create_access_token
from src.app.main import app
from src.app.models.published_service import PublishedService
from src.app.routers.access import get_access_controller
from src.app.schemas.access import ServiceConfig


DRAFT = {
    "name": "Photos",
    "local_ip": "192.168.1.10",
    "local_port": 8080,
    "public_port": 18080,
    "mode": "auto",
    "protocol": "TCP",
    "domain": "example.com",
    "rr": "photos",
}


def headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.username})}"}


@pytest.fixture
def controller():
    value = SimpleNamespace(
        lock=asyncio.Lock(),
        network=None,
        interval=60,
        wake=lambda: None,
        relay=SimpleNamespace(
            status=lambda: {
                "configured": False,
                "available": False,
                "running": False,
                "public_host": None,
                "reason_code": "relay_not_configured",
            },
            apply=AsyncMock(),
        ),
        reconciler=SimpleNamespace(cleanup=AsyncMock(), relay_mapping=lambda r: r.id),
        reconcile=AsyncMock(),
        detect=AsyncMock(return_value={"topology": "unknown"}),
    )
    app.dependency_overrides[get_access_controller] = lambda: value
    yield value
    app.dependency_overrides.pop(get_access_controller, None)


def test_access_requires_active_admin(client, controller, admin_user, normal_user, db_session):
    admin_auth = headers(admin_user)
    assert client.get("/api/access/state").status_code == 401
    assert client.post("/api/access/services", json=DRAFT).status_code == 401
    assert client.get("/api/access/state", headers=headers(normal_user)).status_code == 403
    assert client.post("/api/access/detect", headers=headers(normal_user)).status_code == 403
    admin_user = db_session.merge(admin_user)
    admin_user.is_active = False
    db_session.commit()
    assert client.get("/api/access/state", headers=admin_auth).status_code == 403
    assert db_session.query(PublishedService).count() == 0
    controller.detect.assert_not_awaited()


def test_service_crud_persists_intent_without_claiming_reachability(client, controller, admin_user, db_session):
    auth = headers(admin_user)
    created = client.post("/api/access/services", json=DRAFT, headers=auth)
    assert created.status_code == 200, created.text
    value = created.json()["data"]
    assert value["status"] == "pending" and not value["external_verified"]
    row = db_session.get(PublishedService, value["id"])
    service_id = row.id
    assert row.owner_token and row.domain == "example.com"
    owner = row.owner_token
    response = client.get("/api/access/state", headers=auth)
    assert len(response.json()["data"]["services"]) == 1
    edited = client.put(f"/api/access/services/{row.id}", json={**DRAFT, "enabled": False}, headers=auth)
    assert edited.status_code == 200
    row = db_session.get(PublishedService, service_id)
    assert row.owner_token == owner and row.enabled is False
    deleted = client.delete(f"/api/access/services/{row.id}", headers=auth)
    assert deleted.status_code == 200
    controller.reconciler.cleanup.assert_awaited_once()
    assert db_session.query(PublishedService).count() == 0


def test_port_and_hostname_collisions_are_rejected(client, controller, admin_user):
    auth = headers(admin_user)
    assert client.post("/api/access/services", json=DRAFT, headers=auth).status_code == 200
    duplicate_port = {**DRAFT, "rr": "other"}
    assert client.post("/api/access/services", json=duplicate_port, headers=auth).status_code == 409
    duplicate_dns = {**DRAFT, "public_port": 18081}
    assert client.post("/api/access/services", json=duplicate_dns, headers=auth).status_code == 409
    distinct = {**DRAFT, "public_port": 18081, "rr": "other"}
    assert client.post("/api/access/services", json=distinct, headers=auth).status_code == 200


def test_delete_retains_configuration_when_cleanup_fails(client, controller, admin_user, db_session):
    auth = headers(admin_user)
    service_id = client.post("/api/access/services", json=DRAFT, headers=auth).json()["data"]["id"]
    controller.reconciler.cleanup.side_effect = TimeoutError
    assert client.delete(f"/api/access/services/{service_id}", headers=auth).status_code == 503
    assert db_session.get(PublishedService, service_id) is not None
    controller.relay.apply.assert_not_awaited()


def test_edits_preserve_cleanup_ownership_but_reset_stale_health(client, controller, admin_user, db_session):
    auth = headers(admin_user)
    service_id = client.post("/api/access/services", json=DRAFT, headers=auth).json()["data"]["id"]
    row = db_session.get(PublishedService, service_id)
    row.runtime = {"mapping": {"description": "owned"}, "status": "healthy", "external_verified": True}
    db_session.commit()
    response = client.put(f"/api/access/services/{service_id}", json={**DRAFT, "local_port": 8081}, headers=auth)
    assert response.json()["data"]["external_verified"] is False
    row = db_session.get(PublishedService, service_id)
    assert row.runtime["mapping"] == {"description": "owned"}


@pytest.mark.parametrize(
    "change",
    [
        {"local_ip": "0.0.0.0"},
        {"local_ip": "224.0.0.1"},
        {"local_ip": "127.0.0.1"},
        {"public_port": 0},
        {"lease_duration": 1},
        {"domain": "https://example.com"},
        {"domain": "@"},
        {"rr": "a/b"},
        {"name": " "},
        {"mode": "magic"},
    ],
)
def test_invalid_service_rejected(change):
    with pytest.raises(ValueError):
        ServiceConfig(**{**DRAFT, **change})


def test_relay_loopback_and_explicit_permanent_lease_supported():
    value = ServiceConfig(**{**DRAFT, "local_ip": "127.0.0.1", "mode": "relay", "lease_duration": 0})
    assert value.lease_duration == 0 and value.local_ip == "127.0.0.1"
