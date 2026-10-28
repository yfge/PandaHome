from __future__ import annotations

import asyncio
import socket
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from src.app.services import network_detection
from src.app.services.network_detection import NetworkDetector
from src.app.services.upnp import UPNPService

FIRST_SOURCE = "https://first.example/ip"
SECOND_SOURCE = "https://second.example/ip"


class FakeResponse:
    def __init__(self, body: bytes = b"8.8.8.8", status: int = 200):
        self.body = body
        self.status = status
        self.content = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def iter_chunked(self, size: int):
        for offset in range(0, len(self.body), size):
            yield self.body[offset : offset + size]


class FakeSession:
    def __init__(self):
        self.responses: dict[str, FakeResponse | Exception] = {FIRST_SOURCE: FakeResponse()}
        self.calls: list[tuple[str, dict]] = []
        self.options: dict = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def get(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture()
def http(monkeypatch: pytest.MonkeyPatch) -> FakeSession:
    session = FakeSession()

    def create_session(**options):
        session.options = options
        return session

    monkeypatch.setattr(network_detection.aiohttp, "ClientSession", create_session)
    monkeypatch.setattr(network_detection.aiohttp, "TCPConnector", lambda **options: options)
    return session


def gateway_service(address: object):
    return SimpleNamespace(
        get_external_ip=AsyncMock(return_value=address),
        get_port_mappings=AsyncMock(),
        add_port_mapping=AsyncMock(),
        delete_port_mapping=AsyncMock(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("gateway", "topology", "mode", "reason"),
    [
        ("8.8.8.8", "public_ipv4", "direct", "public_ipv4_candidate"),
        ("1.1.1.1", "upstream_nat", "relay", "public_ip_mismatch"),
        ("100.64.0.1", "cgnat", "relay", "gateway_shared_address"),
        ("100.127.255.254", "cgnat", "relay", "gateway_shared_address"),
        ("10.0.0.1", "upstream_nat", "relay", "gateway_private_address"),
        ("172.16.0.1", "upstream_nat", "relay", "gateway_private_address"),
        ("172.31.255.254", "upstream_nat", "relay", "gateway_private_address"),
        ("192.168.1.1", "upstream_nat", "relay", "gateway_private_address"),
        ("100.63.255.254", "upstream_nat", "relay", "public_ip_mismatch"),
        ("100.128.0.1", "upstream_nat", "relay", "public_ip_mismatch"),
        ("172.32.0.1", "upstream_nat", "relay", "public_ip_mismatch"),
        ("127.0.0.1", "unknown", "unknown", "gateway_address_not_global"),
        ("169.254.1.1", "unknown", "unknown", "gateway_address_not_global"),
        ("203.0.113.1", "unknown", "unknown", "gateway_address_not_global"),
        ("224.0.0.1", "unknown", "unknown", "gateway_address_not_global"),
        ("0.0.0.0", "unknown", "unknown", "gateway_address_not_global"),
    ],
)
async def test_classifies_gateway_evidence(http: FakeSession, gateway, topology, mode, reason):
    service = gateway_service(gateway)
    report = await NetworkDetector(service, public_ip_urls=(FIRST_SOURCE,)).detect()

    assert (report.topology, report.recommended_mode, report.reason_code) == (topology, mode, reason)
    assert report.observed_public_ip == "8.8.8.8"
    assert report.gateway_external_ip == gateway
    assert report.upnp_available is True
    assert report.checked_at.utcoffset() == timedelta(0)
    service.get_external_ip.assert_awaited_once()
    service.get_port_mappings.assert_not_called()
    service.add_port_mapping.assert_not_called()
    service.delete_port_mapping.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"not an IP", b"2001:4860::8888", b"10.0.0.1", b"100.64.0.1", b"224.0.0.1"])
async def test_invalid_or_nonpublic_echo_is_not_used(http: FakeSession, body: bytes):
    http.responses[FIRST_SOURCE] = FakeResponse(body)
    report = await NetworkDetector(gateway_service("8.8.8.8"), public_ip_urls=(FIRST_SOURCE,)).detect()

    assert report.observed_public_ip is None
    assert report.topology == "unknown"
    assert report.recommended_mode == "unknown"
    assert report.reason_code == "public_ip_unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        aiohttp.ClientConnectionError("unreachable"),
        TimeoutError(),
        FakeResponse(status=503),
        FakeResponse(status=302),
        FakeResponse(b"2001:4860::8888"),
        FakeResponse(b"{" + b"x" * 128),
        FakeResponse(b"\xff"),
    ],
)
async def test_echo_failure_uses_next_source(http: FakeSession, failure):
    http.responses = {FIRST_SOURCE: failure, SECOND_SOURCE: FakeResponse(b" 8.8.8.8\n")}
    report = await NetworkDetector(gateway_service("8.8.8.8"), public_ip_urls=(FIRST_SOURCE, SECOND_SOURCE)).detect()

    assert report.topology == "public_ipv4"
    assert [url for url, _ in http.calls] == [FIRST_SOURCE, SECOND_SOURCE]
    assert all(options["allow_redirects"] is False for _, options in http.calls)
    assert http.options["timeout"].total == network_detection.HTTP_TIMEOUT_SECONDS
    assert http.options["connector"]["family"] == socket.AF_INET
    assert http.options["trust_env"] is False


@pytest.mark.asyncio
async def test_valid_echo_stops_fallback(http: FakeSession):
    report = await NetworkDetector(gateway_service("8.8.8.8"), public_ip_urls=(FIRST_SOURCE, SECOND_SOURCE)).detect()

    assert report.observed_public_ip == "8.8.8.8"
    assert [url for url, _ in http.calls] == [FIRST_SOURCE]


@pytest.mark.asyncio
@pytest.mark.parametrize("gateway", ["100.64.0.1", "192.168.1.1"])
async def test_private_gateway_is_evidence_without_public_echo(http: FakeSession, gateway: str):
    http.responses[FIRST_SOURCE] = TimeoutError()
    report = await NetworkDetector(gateway_service(gateway), public_ip_urls=(FIRST_SOURCE,)).detect()

    assert report.observed_public_ip is None
    assert report.recommended_mode == "relay"
    assert report.topology in {"cgnat", "upstream_nat"}


@pytest.mark.asyncio
@pytest.mark.parametrize("address", [None, "invalid", "::1", 123, [], {"external_ip": "8.8.8.8"}])
async def test_invalid_gateway_address_remains_unknown(http: FakeSession, address):
    report = await NetworkDetector(gateway_service(address), public_ip_urls=(FIRST_SOURCE,)).detect()

    assert report.topology == "unknown"
    assert report.gateway_external_ip is None
    assert report.upnp_available is True
    assert report.reason_code == "gateway_ip_unavailable"


@pytest.mark.asyncio
async def test_gateway_failure_does_not_discard_public_echo(http: FakeSession):
    service = gateway_service(None)
    service.get_external_ip.side_effect = RuntimeError("discovery unavailable")
    report = await NetworkDetector(service, public_ip_urls=(FIRST_SOURCE,)).detect()

    assert report.observed_public_ip == "8.8.8.8"
    assert report.gateway_external_ip is None
    assert report.upnp_available is False
    assert report.recommended_mode == "unknown"


@pytest.mark.asyncio
async def test_gateway_timeout_is_bounded(http: FakeSession, monkeypatch: pytest.MonkeyPatch):
    service = gateway_service(None)

    async def wait_forever():
        await asyncio.Event().wait()

    service.get_external_ip.side_effect = wait_forever
    monkeypatch.setattr(network_detection, "GATEWAY_TIMEOUT_SECONDS", 0.01)
    report = await NetworkDetector(service, public_ip_urls=(FIRST_SOURCE,)).detect()

    assert report.upnp_available is False
    assert report.reason_code == "upnp_unavailable"


@pytest.mark.asyncio
async def test_shutdown_cancellation_propagates(http: FakeSession):
    service = gateway_service(None)
    service.get_external_ip.side_effect = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await NetworkDetector(service, public_ip_urls=(FIRST_SOURCE,)).detect()


@pytest.mark.parametrize("url", ["http://api.ipify.org", "https:///ip", "https://user:password@example.com"])
def test_echo_sources_require_https_without_credentials(url: str):
    with pytest.raises(ValueError, match="HTTPS"):
        NetworkDetector(gateway_service(None), public_ip_urls=(url,))


@pytest.mark.asyncio
async def test_discovered_gateway_requires_exact_host_match():
    upnp = UPNPService()
    upnp.initialized = True
    upnp.gateway_info = {"ip": "192.168.1.1"}
    upnp.devices = [
        {"LOCATION": "http://192.168.1.10:1900/description.xml"},
        {"LOCATION": "http://192.168.1.1:1900/description.xml"},
    ]
    action = object()
    upnp.upnp = SimpleNamespace(async_create_device=AsyncMock(return_value=object()))
    upnp.find_wan_ip_service = Mock(return_value=action)
    assert await upnp.gateway_service() is action
    upnp.upnp.async_create_device.assert_awaited_once_with("http://192.168.1.1:1900/description.xml")
