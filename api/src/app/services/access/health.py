"""Bounded local checks and optional standard blackbox-exporter probes."""

import asyncio
import ipaddress
import re
from urllib.parse import urlsplit

import aiohttp

from ..ssh_probe import load_ssh_probe


async def local_tcp(host: str, port: int) -> bool:
    try:
        async with asyncio.timeout(3):
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
        return True
    except (OSError, TimeoutError):
        return False


def validate_remote_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Use an HTTPS remote URL without embedded credentials or fragments.")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        if parsed.hostname.lower() in {"localhost", "localhost.localdomain"}:
            raise ValueError("The public probe or webhook must be on a remote host.")
    else:
        if not address.is_global:
            raise ValueError("The public probe or webhook must be on a remote host.")


class HealthChecks:
    def __init__(self, *, probe_url: str = "", webhook_url: str = "", probe_provider: str = "https",
                 probe_ssh_config_file: str = ""):
        for url in (probe_url, webhook_url):
            if url:
                validate_remote_url(url)
        self.probe_url = probe_url
        self.webhook_url = webhook_url
        if probe_provider not in {"https", "ssh"}:
            raise ValueError("Unknown external probe provider")
        self._ssh_probe = load_ssh_probe(probe_ssh_config_file) if probe_provider == "ssh" else None

    async def local(self, row) -> bool | None:
        return await local_tcp(row.local_ip, row.local_port) if row.protocol == "TCP" else None

    async def external(self, host: str, port: int, protocol: str) -> bool | None:
        if protocol != "TCP":
            return None
        if self._ssh_probe is not None:
            return await self._ssh_probe.external(host, port)
        if not self.probe_url:
            return None
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(
                    self.probe_url,
                    params={"target": f"{host}:{port}", "module": "tcp_connect"},
                    allow_redirects=False,
                ) as response:
                    if response.status != 200:
                        return False
                    try:
                        body = await response.content.readexactly(131073)
                    except asyncio.IncompleteReadError as error:
                        body = error.partial
                    if len(body) > 131072:
                        return False
                    return bool(re.search(rb"^probe_success(?:\{[^\n]*\})?\s+1(?:\.0)?\s*$", body, re.MULTILINE))
        except (aiohttp.ClientError, TimeoutError):
            return False

    async def notify(self, *, service_id: int, name: str, event: str, reason: str | None) -> bool:
        if not self.webhook_url:
            return False
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(
                    self.webhook_url,
                    json={"service_id": service_id, "name": name, "event": event, "reason_code": reason},
                    allow_redirects=False,
                ) as response:
                    return 200 <= response.status < 300
        except (aiohttp.ClientError, TimeoutError):
            return False
