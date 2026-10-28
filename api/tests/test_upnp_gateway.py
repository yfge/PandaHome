import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from async_upnp_client.exceptions import UpnpActionError
from pydantic import ValidationError

from src.app.auth.auth import create_access_token
from src.app.main import app
from src.app.schemas.upnp_gateway import GatewayInfo, GatewayMappingCreate, GatewayTarget
from src.app.services import upnp_gateway
from src.app.services.upnp_gateway import GatewayError, address_scope, open_gateway

OUTER = "http://192.168.1.1:5000/rootDesc.xml"
INNER = "http://192.168.2.1:5000/rootDesc.xml"
PREFIX = "/api/upnp/gateways"


class FakeWAN:
    def __init__(self, address, service_type="WANIPConnection:1"):
        self.service_type = f"urn:schemas-upnp-org:service:{service_type}"
        self.address = address
        self.rules = {}
        self.enumeration_supported = True
        self.fail_enumeration = False
        self.specific_supported = True
        self.missing_actions = set()
        self.mutations = []

    def has_action(self, action):
        return action not in self.missing_actions

    async def async_call_action(self, action, **params):
        await asyncio.sleep(0)
        if action == "GetExternalIPAddress":
            return {"NewExternalIPAddress": self.address}
        if action == "GetGenericPortMappingEntry":
            if self.fail_enumeration:
                raise OSError("Connection lost")
            if not self.enumeration_supported:
                raise UpnpActionError(error_code=401)
            try:
                return list(self.rules.values())[params["NewPortMappingIndex"]]
            except IndexError:
                raise UpnpActionError(error_code=713) from None
        key = (params["NewExternalPort"], params["NewProtocol"])
        if action == "GetSpecificPortMappingEntry":
            if not self.specific_supported:
                raise UpnpActionError(error_code=401)
            if key not in self.rules:
                raise UpnpActionError(error_code=714)
            return self.rules[key]
        if action == "AddPortMapping":
            self.mutations.append((action, params))
            self.rules[key] = params
            return {}
        if action == "DeletePortMapping":
            if key not in self.rules:
                raise UpnpActionError(error_code=714)
            self.mutations.append((action, params))
            del self.rules[key]
            return {}
        raise AssertionError(action)


@pytest.fixture()
def routers(monkeypatch):
    outer = FakeWAN("8.8.8.8", "WANPPPConnection:1")
    inner = FakeWAN("192.168.1.2", "WANIPConnection:2")
    devices = {
        OUTER: SimpleNamespace(all_services=[outer], friendly_name="Public router"),
        INNER: SimpleNamespace(all_services=[inner], friendly_name="Inner router"),
    }
    create = AsyncMock(side_effect=lambda location: devices[location])
    monkeypatch.setattr(upnp_gateway, "UpnpFactory", lambda requester: SimpleNamespace(async_create_device=create))
    default_service = SimpleNamespace(
        devices=[{"LOCATION": INNER}, {"location": OUTER}, {"location": OUTER}],
        gateway_info={"ip": "192.168.2.1"}, interface_ip="192.168.2.10",
    )
    monkeypatch.setattr(app.state, "upnp_service", default_service)
    return outer, inner, create


@pytest.fixture()
def admin_headers(admin_user):
    return {"Authorization": f"Bearer {create_access_token({'sub': admin_user.username})}"}


def payload(address="192.168.1.2"):
    return {"external_port": 8080, "internal_port": 80, "protocol": "TCP", "local_ip": address}


def test_discover_and_inspect_upstream_without_default_selection(client, routers, admin_headers):
    response = client.get(PREFIX, headers=admin_headers)
    assert response.status_code == 200, response.text
    gateways = {item["device_url"]: item for item in response.json()["data"]["gateways"]}
    assert len(gateways) == 2
    assert gateways[OUTER]["address_scope"] == "public"
    assert gateways[INNER]["address_scope"] == "private"
    assert gateways[INNER]["is_default"] is True
    assert gateways[OUTER]["is_default"] is False
    response = client.post(f"{PREFIX}/inspect", json={"device_url": OUTER}, headers=admin_headers)
    assert response.json()["data"]["device_url"] == OUTER
    assert app.state.upnp_service.gateway_info["ip"] == "192.168.2.1"
    assert not routers[0].mutations and not routers[1].mutations


def test_mapping_crud_uses_exact_selected_router(client, routers, admin_headers):
    params = {"device_url": OUTER}
    response = client.post(f"{PREFIX}/mappings", params=params, json=payload(), headers=admin_headers)
    assert response.status_code == 200, response.text
    response = client.get(f"{PREFIX}/mappings", params=params, headers=admin_headers)
    assert response.json()["data"]["mappings"][0]["internal_ip"] == "192.168.1.2"
    assert not routers[1].mutations
    response = client.delete(f"{PREFIX}/mappings/8080", params=params, headers=admin_headers)
    assert response.status_code == 200
    assert not routers[0].rules
    assert not routers[1].mutations


def test_existing_mapping_is_preserved(client, routers, admin_headers):
    params = {"device_url": OUTER}
    assert client.post(f"{PREFIX}/mappings", params=params, json=payload(), headers=admin_headers).status_code == 200
    response = client.post(f"{PREFIX}/mappings", params=params, json=payload("192.168.1.99"), headers=admin_headers)
    assert response.status_code == 409
    assert routers[0].rules[(8080, "TCP")]["NewInternalClient"] == "192.168.1.2"


def test_enumeration_optional_for_add_and_delete(client, routers, admin_headers):
    routers[0].enumeration_supported = False
    params = {"device_url": OUTER}
    response = client.get(f"{PREFIX}/mappings", params=params, headers=admin_headers)
    assert response.json()["data"]["enumeration_supported"] is False
    assert client.post(f"{PREFIX}/mappings", params=params, json=payload(), headers=admin_headers).status_code == 200
    assert client.delete(f"{PREFIX}/mappings/8080", params=params, headers=admin_headers).status_code == 200


def test_failed_collision_check_does_not_write(client, routers, admin_headers):
    routers[0].specific_supported = False
    response = client.post(
        f"{PREFIX}/mappings", params={"device_url": OUTER}, json=payload(), headers=admin_headers,
    )
    assert response.status_code == 502
    assert not routers[0].mutations


def test_actions_absent_from_device_description_are_handled(client, routers, admin_headers):
    routers[0].missing_actions = {"GetGenericPortMappingEntry", "GetSpecificPortMappingEntry"}
    params = {"device_url": OUTER}
    response = client.get(f"{PREFIX}/mappings", params=params, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["data"]["enumeration_supported"] is False
    response = client.post(f"{PREFIX}/mappings", params=params, json=payload(), headers=admin_headers)
    assert response.status_code == 502
    assert not routers[0].mutations


def test_unreachable_target_never_falls_back(client, routers, admin_headers):
    response = client.post(f"{PREFIX}/inspect", json={"device_url": "http://192.168.3.1/igd.xml"}, headers=admin_headers)
    assert response.status_code == 502
    assert routers[2].await_args.args == ("http://192.168.3.1/igd.xml",)
    assert not routers[0].mutations and not routers[1].mutations


def test_broken_enumeration_is_an_error_not_an_empty_table(client, routers, admin_headers):
    routers[0].fail_enumeration = True
    response = client.get(f"{PREFIX}/mappings", params={"device_url": OUTER}, headers=admin_headers)
    assert response.status_code == 502


def test_target_and_mapping_validation(client, routers, admin_headers):
    assert client.get(f"{PREFIX}/mappings", headers=admin_headers).status_code == 422
    for value in ("file:///etc/passwd", "http://user:password@192.168.1.1/igd.xml", f"{OUTER}#fragment"):
        response = client.post(f"{PREFIX}/inspect", json={"device_url": value}, headers=admin_headers)
        assert response.status_code == 422, response.text
    for change in (
        {"local_ip": ""}, {"local_ip": "::1"}, {"lease_duration": -1},
        {"lease_duration": 4294967296}, {"enabled": False},
    ):
        response = client.post(
            f"{PREFIX}/mappings", params={"device_url": OUTER}, json={**payload(), **change}, headers=admin_headers,
        )
        assert response.status_code == 422, response.text
    assert not routers[0].mutations


def test_new_endpoints_require_admin(client, routers, normal_user):
    headers = {"Authorization": f"Bearer {create_access_token({'sub': normal_user.username})}"}
    for method, path, body in (
        ("GET", PREFIX, None), ("POST", f"{PREFIX}/inspect", {"device_url": OUTER}),
        ("GET", f"{PREFIX}/mappings", None), ("POST", f"{PREFIX}/mappings", payload()),
        ("DELETE", f"{PREFIX}/mappings/8080", None),
    ):
        assert client.request(method, path, params={"device_url": OUTER}, json=body).status_code == 401
        assert client.request(method, path, params={"device_url": OUTER}, json=body, headers=headers).status_code == 403
    assert not routers[0].mutations and not routers[1].mutations


def test_new_endpoints_reject_inactive_admin(client, routers, admin_user, db_session):
    headers = {"Authorization": f"Bearer {create_access_token({'sub': admin_user.username})}"}
    admin_user.is_active = False
    db_session.commit()
    assert client.get(PREFIX, headers=headers).status_code == 403
    assert client.post(f"{PREFIX}/mappings", params={"device_url": OUTER}, json=payload(), headers=headers).status_code == 403
    assert client.delete(f"{PREFIX}/mappings/8080", params={"device_url": OUTER}, headers=headers).status_code == 403


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_failed_target_mutation_never_falls_back(client, routers, admin_headers, method):
    original = routers[0].async_call_action

    async def failed(action, **params):
        if action in {"AddPortMapping", "DeletePortMapping"}:
            raise OSError("Selected router connection lost")
        return await original(action, **params)

    routers[0].async_call_action = failed
    path = f"{PREFIX}/mappings" + ("/8080" if method == "DELETE" else "")
    response = client.request(method, path, params={"device_url": OUTER}, json=payload(), headers=admin_headers)
    assert response.status_code == 502
    assert not routers[0].mutations and not routers[1].mutations


def test_tcp_udp_rules_and_router_ownership_are_independent(client, routers, admin_headers):
    for location in (OUTER, INNER):
        for protocol in ("TCP", "UDP"):
            response = client.post(
                f"{PREFIX}/mappings", params={"device_url": location},
                json={**payload(), "protocol": protocol}, headers=admin_headers,
            )
            assert response.status_code == 200
    response = client.delete(f"{PREFIX}/mappings/8080", params={"device_url": OUTER, "protocol": "UDP"}, headers=admin_headers)
    assert response.status_code == 200
    assert (8080, "TCP") in routers[0].rules and (8080, "UDP") not in routers[0].rules
    assert set(routers[1].rules) == {(8080, "TCP"), (8080, "UDP")}
    assert client.delete(f"{PREFIX}/mappings/8080", params={"device_url": OUTER, "protocol": "UDP"}, headers=admin_headers).status_code == 404


def test_mapping_enumeration_is_bounded(client, routers, admin_headers, monkeypatch):
    monkeypatch.setattr(upnp_gateway, "MAX_MAPPINGS", 1)
    params = {"device_url": OUTER}
    for protocol in ("TCP", "UDP"):
        assert client.post(
            f"{PREFIX}/mappings", params=params, json={**payload(), "protocol": protocol}, headers=admin_headers,
        ).status_code == 200
    result = client.get(f"{PREFIX}/mappings", params=params, headers=admin_headers).json()["data"]
    assert len(result["mappings"]) == 1 and result["complete"] is False


@pytest.mark.asyncio
async def test_concurrent_targets_do_not_share_state(routers):
    async def add(location, address):
        async with open_gateway(location) as gateway:
            await gateway.add_mapping(GatewayMappingCreate(**payload(address)))
    await asyncio.gather(add(OUTER, "192.168.1.2"), add(INNER, "192.168.2.10"))
    assert routers[0].rules[(8080, "TCP")]["NewInternalClient"] == "192.168.1.2"
    assert routers[1].rules[(8080, "TCP")]["NewInternalClient"] == "192.168.2.10"


@pytest.mark.asyncio
async def test_client_sessions_close_on_failure(monkeypatch):
    sessions = []
    original_session = upnp_gateway.aiohttp.ClientSession

    def session(**kwargs):
        result = original_session(**kwargs)
        sessions.append(result)
        return result

    monkeypatch.setattr(upnp_gateway.aiohttp, "ClientSession", session)
    monkeypatch.setattr(upnp_gateway, "UpnpFactory", lambda requester: SimpleNamespace(
        async_create_device=AsyncMock(side_effect=OSError("unreachable")),
    ))
    with pytest.raises(GatewayError):
        async with open_gateway(OUTER):
            pytest.fail("unreachable IGD was opened")
    assert sessions and all(item.closed for item in sessions)


@pytest.mark.asyncio
async def test_operation_deadline_cancels_a_stalled_device_load(monkeypatch):
    monkeypatch.setattr(upnp_gateway, "OPERATION_TIMEOUT_SECONDS", 0.01)
    cancelled = asyncio.Event()

    async def stalled(location):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(upnp_gateway, "UpnpFactory", lambda requester: SimpleNamespace(async_create_device=stalled))
    with pytest.raises(GatewayError) as failure:
        async with open_gateway(OUTER):
            pytest.fail("Timed-out IGD was opened")
    assert failure.value.status_code == 504 and cancelled.is_set()


@pytest.mark.asyncio
async def test_http_request_timeout_against_a_local_stalled_server(monkeypatch):
    release = asyncio.Event()
    requested = asyncio.Event()

    async def stalled(request):
        requested.set()
        await release.wait()
        return web.Response(text="not a device")

    server = web.Application()
    server.router.add_get("/device.xml", stalled)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    monkeypatch.setattr(upnp_gateway, "HTTP_TIMEOUT_SECONDS", 0.02)
    try:
        async with asyncio.timeout(1):
            with pytest.raises(GatewayError):
                async with open_gateway(f"http://127.0.0.1:{port}/device.xml"):
                    pytest.fail("Stalled HTTP response was accepted")
        assert requested.is_set()
    finally:
        release.set()
        await runner.cleanup()


@pytest.mark.asyncio
async def test_ssdp_deadline_retains_known_devices(monkeypatch, routers):
    async def stalled(*args, **kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(upnp_gateway, "SSDP_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(upnp_gateway, "async_search", stalled)
    result = await upnp_gateway.discover_gateways(app.state.upnp_service, refresh=True)
    assert result["discovery_error"] and len(result["gateways"]) == 2
    assert not routers[0].mutations and not routers[1].mutations


@pytest.mark.asyncio
async def test_discovery_inspection_is_bounded(monkeypatch):
    inspected = []

    async def many_devices(callback, **kwargs):
        for index in range(30):
            await callback({"location": f"http://192.168.1.{index + 1}/device.xml"})

    @asynccontextmanager
    async def fake_gateway(location):
        inspected.append(location)
        yield SimpleNamespace(info=AsyncMock(return_value=GatewayInfo(device_url=location, host="router")))

    monkeypatch.setattr(upnp_gateway, "MAX_GATEWAYS", 2)
    monkeypatch.setattr(upnp_gateway, "async_search", many_devices)
    monkeypatch.setattr(upnp_gateway, "open_gateway", fake_gateway)
    result = await upnp_gateway.discover_gateways(SimpleNamespace(devices=[]), refresh=True)
    assert len(result["gateways"]) == 2 and len(inspected) == 2


@pytest.mark.parametrize(("address", "scope"), [
    ("8.8.8.8", "public"), ("192.168.1.2", "private"), ("172.16.0.1", "private"),
    ("100.64.0.1", "shared"), ("100.127.255.254", "shared"), (None, "unknown"),
    ("0.0.0.0", "unknown"), ("203.0.113.1", "unknown"), ("::1", "unknown"), ("224.0.0.1", "unknown"),
])
def test_address_scope_does_not_treat_every_non_private_address_as_public(address, scope):
    assert address_scope(address) == scope


def test_url_preserves_device_description_query():
    assert str(GatewayTarget(device_url=f"{OUTER}?device=1").device_url) == f"{OUTER}?device=1"
    with pytest.raises(ValidationError):
        GatewayTarget(device_url="not a URL")
