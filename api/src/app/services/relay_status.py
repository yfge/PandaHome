"""Read owned proxy registration from frpc's authenticated loopback API."""

import asyncio
import json
import secrets
import socket
from collections.abc import Mapping

import aiohttp


class FrpStatusClient:
    _RETRY_WINDOW = 1.0
    _BODY_LIMIT = 262144

    def __init__(self):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            self._port = reservation.getsockname()[1]
        self._password = secrets.token_urlsafe(32)

    def configuration(self) -> str:
        # Generated URL-safe credentials need no additional TOML escaping.
        return (
            'webServer.addr = "127.0.0.1"\n'
            f"webServer.port = {self._port}\n"
            'webServer.user = "pandahome"\n'
            f'webServer.password = "{self._password}"\n'
        )

    async def registration(self, expected: Mapping[str, int]) -> dict[int, bool]:
        """Wait briefly for native startup; failures never count as accepted."""
        result = {service_id: False for service_id in expected.values()}
        if not expected:
            return result
        try:
            async with asyncio.timeout(self._RETRY_WINDOW):
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0.3), trust_env=False) as session:
                    while True:
                        result = await self._read(session, expected)
                        if all(result.values()):
                            return result
                        await asyncio.sleep(0.05)
        except TimeoutError:
            return result

    async def _read(self, session, expected: Mapping[str, int]) -> dict[int, bool]:
        failed = {service_id: False for service_id in expected.values()}
        try:
            async with session.get(
                f"http://127.0.0.1:{self._port}/api/status",
                auth=aiohttp.BasicAuth("pandahome", self._password),
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return failed
                try:
                    body = await response.content.readexactly(self._BODY_LIMIT + 1)
                except asyncio.IncompleteReadError as error:
                    body = error.partial
                if len(body) > self._BODY_LIMIT:
                    return failed
                return _registrations(json.loads(body), expected)
        except (aiohttp.ClientError, TimeoutError, ValueError, UnicodeError):
            return failed


def _registrations(payload, expected: Mapping[str, int]) -> dict[int, bool]:
    accepted, seen = {}, set()
    if isinstance(payload, dict):
        for protocol in ("tcp", "udp"):
            rows = payload.get(protocol)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict) or not isinstance(name := row.get("name"), str):
                    continue
                if name not in expected or not name.endswith(f"-{protocol}"):
                    continue
                accepted[name] = (
                    name not in seen
                    and row.get("type") == protocol
                    and row.get("status") == "running"
                    and row.get("err", "") == ""
                )
                seen.add(name)
    result = dict.fromkeys(expected.values(), True)
    for name, service_id in expected.items():
        result[service_id] &= accepted.get(name, False)
    return result
