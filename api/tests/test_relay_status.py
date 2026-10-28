import asyncio
import base64
import json
import tomllib
from contextlib import asynccontextmanager

import pytest
from aiohttp import web

from src.app.services.relay_status import FrpStatusClient


@asynccontextmanager
async def native_status_endpoint(handler):
    client = FrpStatusClient()
    client._RETRY_WINDOW = 0.04
    config = tomllib.loads(client.configuration())["webServer"]
    application = web.Application()
    application.router.add_route("*", "/{tail:.*}", handler)
    runner = web.AppRunner(application)
    await runner.setup()
    site = web.TCPSite(runner, config["addr"], config["port"])
    await site.start()
    try:
        yield client, config
    finally:
        await runner.cleanup()


def proxy(name="pandahome-1-tcp", *, protocol="tcp", status="running", error=""):
    return {"name": name, "type": protocol, "status": status, "err": error}


@pytest.mark.asyncio
async def test_authenticated_native_status_ignores_unrelated_proxy_names():
    observed = []

    async def handler(request):
        observed.append((request.method, request.path, request.headers.get("Authorization")))
        return web.json_response(
            {
                "tcp": [proxy(), proxy("pandahome-999-tcp"), proxy("unrelated-tcp")],
                "udp": [proxy("pandahome-2-udp", protocol="udp")],
            }
        )

    async with native_status_endpoint(handler) as (client, config):
        expected = {"pandahome-1-tcp": 1, "pandahome-2-udp": 2}
        assert await client.registration(expected) == {1: True, 2: True}
        credentials = base64.b64encode(f"pandahome:{config['password']}".encode()).decode()
        assert observed == [("GET", "/api/status", f"Basic {credentials}")]
        assert config["password"] not in repr(client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,error",
    [("start error", "port already used"), ("wait start", ""), ("closed", ""), ("running", "not accepted")],
)
async def test_native_proxy_must_be_running_without_error(status, error):
    async def handler(request):
        return web.json_response({"tcp": [proxy(status=status, error=error)]})

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}


@pytest.mark.asyncio
@pytest.mark.parametrize("udp_status,expected", [("running", True), ("start error", False)])
async def test_service_requires_every_requested_protocol_to_be_accepted(udp_status, expected):
    async def handler(request):
        return web.json_response(
            {"tcp": [proxy()], "udp": [proxy("pandahome-1-udp", protocol="udp", status=udp_status)]}
        )

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1, "pandahome-1-udp": 1}) == {1: expected}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        {"tcp": None},
        {"tcp": ["invalid entry"]},
        {"tcp": [proxy(), proxy()]},
        {"tcp": [proxy(protocol="udp")]},
        {"udp": [proxy()]},
        {"tcp": [{"name": []}]},
    ],
)
async def test_missing_malformed_or_duplicate_proxy_is_not_registered(payload):
    async def handler(request):
        return web.json_response(payload)

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [302, 401, 500])
async def test_native_http_errors_or_redirects_never_claim_acceptance(status):
    paths = []

    async def handler(request):
        paths.append(request.path)
        return web.json_response({"tcp": [proxy()]}, status=status, headers={"Location": "/wrong"})

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}
    assert paths and set(paths) == {"/api/status"}


@pytest.mark.asyncio
async def test_status_waits_for_fragmented_json_before_parsing():
    async def handler(request):
        response = web.StreamResponse()
        await response.prepare(request)
        await response.write(b'{"tcp": ')
        await asyncio.sleep(0.01)
        await response.write(json.dumps([proxy()]).encode() + b"}")
        await response.write_eof()
        return response

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: True}


@pytest.mark.asyncio
async def test_oversized_status_body_is_rejected_even_with_early_valid_json():
    async def handler(request):
        response = web.StreamResponse()
        await response.prepare(request)
        await response.write(json.dumps({"tcp": [proxy()]}).encode())
        await asyncio.sleep(0.01)
        try:
            await response.write(b" " * 262144)
            await response.write_eof()
        except ConnectionResetError:
            pass
        return response

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}


@pytest.mark.asyncio
async def test_truncated_http_status_body_is_rejected():
    async def handler(request):
        response = web.StreamResponse(headers={"Content-Length": "1000"})
        await response.prepare(request)
        await response.write(json.dumps({"tcp": [proxy()]}).encode())
        await asyncio.sleep(0.01)
        request.transport.close()
        return response

    async with native_status_endpoint(handler) as (client, _):
        assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}


@pytest.mark.asyncio
async def test_unavailable_status_is_bounded_and_empty_desired_set_needs_no_request():
    client = FrpStatusClient()
    client._RETRY_WINDOW = 0.04
    start = asyncio.get_running_loop().time()
    assert await client.registration({}) == {}
    assert await client.registration({"pandahome-1-tcp": 1}) == {1: False}
    assert asyncio.get_running_loop().time() - start < 0.5


def test_status_endpoint_credentials_are_random_for_each_adapter():
    first = tomllib.loads(FrpStatusClient().configuration())["webServer"]
    second = tomllib.loads(FrpStatusClient().configuration())["webServer"]
    assert first["addr"] == second["addr"] == "127.0.0.1"
    assert first["password"] != second["password"]
