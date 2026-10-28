import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiohttp
import pytest
from aiohttp import web

import src.app.services.access.health as health_module
from src.app.services.access.health import HealthChecks, local_tcp, validate_remote_url


@asynccontextmanager
async def http_endpoint(handler):
    application = web.Application()
    application.router.add_route("*", "/{tail:.*}", handler)
    runner = web.AppRunner(application)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


def checks_for_local_endpoint(origin, *, probe_path="/probe", webhook_path=""):
    # Production validates remote HTTPS URLs. Point only these test instances
    # at the controlled loopback server to exercise real HTTP stream behavior.
    checks = HealthChecks()
    checks.probe_url = origin + probe_path if probe_path else ""
    checks.webhook_url = origin + webhook_path if webhook_path else ""
    return checks


@pytest.mark.asyncio
async def test_local_tcp_connects_to_actual_listener_and_detects_closed_port():
    accepted = asyncio.Event()

    async def accept(reader, writer):
        accepted.set()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(accept, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        assert await local_tcp("127.0.0.1", port) is True
        await asyncio.wait_for(accepted.wait(), 1)
    finally:
        server.close()
        await server.wait_closed()
    assert await local_tcp("127.0.0.1", port) is False


@pytest.mark.asyncio
async def test_tcp_timeout_is_reported_as_failed(monkeypatch):
    monkeypatch.setattr(health_module.asyncio, "open_connection", AsyncMock(side_effect=TimeoutError))
    assert await local_tcp("192.168.1.50", 8080) is False


@pytest.mark.asyncio
async def test_unavailable_probe_and_udp_remain_unverified(monkeypatch):
    connect = AsyncMock()
    monkeypatch.setattr(health_module, "local_tcp", connect)
    checks = HealthChecks()
    assert await checks.external("public.example.com", 18080, "TCP") is None
    assert await checks.external("public.example.com", 18080, "UDP") is None
    assert await checks.local(SimpleNamespace(local_ip="192.168.1.50", local_port=8080, protocol="UDP")) is None
    connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_blackbox_keeps_custom_path_and_query_and_parses_labeled_metric():
    observed = []

    async def handler(request):
        observed.append((request.path, dict(request.query)))
        return web.Response(
            body=b'# HELP probe_success Whether the probe succeeded\nprobe_success{region="external"} 1\n'
        )

    async with http_endpoint(handler) as origin:
        checks = checks_for_local_endpoint(origin, probe_path="/monitoring/probe?tenant=home")
        assert await checks.external("home.example.com", 18080, "TCP") is True
    assert observed == [
        ("/monitoring/probe", {"tenant": "home", "target": "home.example.com:18080", "module": "tcp_connect"})
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body", [b"probe_success 0\n", b"other_probe_success 1\n", b"# probe_success 1\n", b"html error"]
)
async def test_failed_or_unrecognized_metric_is_not_success(body):
    async def handler(request):
        return web.Response(body=body)

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is False


@pytest.mark.asyncio
async def test_probe_waits_for_fragmented_metric_until_response_end():
    async def handler(request):
        response = web.StreamResponse()
        await response.prepare(request)
        await response.write(b"# HELP probe_success Whether the probe succeeded\n")
        await asyncio.sleep(0.01)
        await response.write(b"probe_success 1\n")
        await response.write_eof()
        return response

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is True


@pytest.mark.asyncio
async def test_probe_rejects_oversized_body_even_if_early_fragment_claims_success():
    async def handler(request):
        response = web.StreamResponse()
        await response.prepare(request)
        await response.write(b"probe_success 1\n")
        await asyncio.sleep(0.01)
        try:
            await response.write(b"#" * 131072)
            await response.write_eof()
        except ConnectionResetError:
            pass
        return response

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is False


@pytest.mark.asyncio
async def test_probe_rejects_truncated_http_body_even_with_success_metric():
    async def handler(request):
        response = web.StreamResponse(headers={"Content-Length": "1000"})
        await response.prepare(request)
        await response.write(b"probe_success 1\n")
        await asyncio.sleep(0.01)
        request.transport.close()
        return response

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [302, 401, 500])
async def test_http_failure_does_not_become_success_or_follow_redirect(status):
    requested_paths = []

    async def handler(request):
        requested_paths.append(request.path)
        return web.Response(status=status, body=b"probe_success 1\n", headers={"Location": "/redirected"})

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is False
    assert requested_paths == ["/probe"]


@pytest.mark.asyncio
async def test_external_timeout_is_failed_and_bounded(monkeypatch):
    timeout = aiohttp.ClientTimeout
    monkeypatch.setattr(health_module.aiohttp, "ClientTimeout", lambda **kwargs: timeout(total=0.02))

    async def handler(request):
        await asyncio.sleep(0.1)
        return web.Response(body=b"probe_success 1\n")

    async with http_endpoint(handler) as origin:
        assert await checks_for_local_endpoint(origin).external("home.example.com", 18080, "TCP") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status, expected", [(204, True), (302, False), (400, False), (503, False)])
async def test_webhook_returns_delivery_result_with_meaningful_payload(status, expected):
    observed = []

    async def handler(request):
        observed.append((request.path, await request.json()))
        return web.Response(status=status, headers={"Location": "/redirected"})

    async with http_endpoint(handler) as origin:
        checks = checks_for_local_endpoint(origin, probe_path="", webhook_path="/events")
        assert (
            await checks.notify(service_id=7, name="Home NAS", event="unavailable", reason="mapping_failed") is expected
        )
    assert observed == [
        ("/events", {"service_id": 7, "name": "Home NAS", "event": "unavailable", "reason_code": "mapping_failed"})
    ]


@pytest.mark.asyncio
async def test_webhook_without_configuration_does_not_claim_delivery():
    assert await HealthChecks().notify(service_id=1, name="Home NAS", event="recovered", reason=None) is False


@pytest.mark.asyncio
async def test_webhook_network_error_is_failed(monkeypatch):
    timeout = aiohttp.ClientTimeout
    monkeypatch.setattr(health_module.aiohttp, "ClientTimeout", lambda **kwargs: timeout(total=0.02))

    async def handler(request):
        await asyncio.sleep(0.1)
        return web.Response(status=204)

    async with http_endpoint(handler) as origin:
        checks = checks_for_local_endpoint(origin, probe_path="", webhook_path="/events")
        assert await checks.notify(service_id=1, name="Home NAS", event="recovered", reason=None) is False


@pytest.mark.parametrize(
    "url",
    [
        "http://probe.example.com/probe",
        "https://user:password@probe.example.com/probe",
        "https://probe.example.com/probe#fragment",
        "https://127.0.0.1/probe",
        "https://192.168.1.1/probe",
        "https://[::1]/probe",
        "https://localhost/probe",
    ],
)
def test_remote_probe_configuration_rejects_local_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        validate_remote_url(url)


def test_remote_probe_configuration_accepts_https_path_and_query():
    validate_remote_url("https://probe.example.com/monitoring/probe?tenant=home")
