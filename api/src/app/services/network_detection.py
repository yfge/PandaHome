from __future__ import annotations

import asyncio
import socket
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv4Network
from urllib.parse import urlsplit

import aiohttp

from ..schemas.network import ConnectionMode, NetworkReport, NetworkTopology
from .upnp import UPNPService

PUBLIC_IP_URLS = ("https://api.ipify.org", "https://checkip.amazonaws.com")
HTTP_TIMEOUT_SECONDS = 4
GATEWAY_TIMEOUT_SECONDS = 8
MAX_IP_RESPONSE_BYTES = 64
SHARED_ADDRESS_SPACE = IPv4Network("100.64.0.0/10")
PRIVATE_NETWORKS = tuple(IPv4Network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


def _ipv4(value: object) -> IPv4Address | None:
    if not isinstance(value, str):
        return None
    try:
        return IPv4Address(value.strip())
    except ValueError:
        return None


def _classify(
    observed: IPv4Address | None, gateway: IPv4Address | None, upnp_available: bool
) -> tuple[NetworkTopology, ConnectionMode, str]:
    if gateway is None:
        reason = "gateway_ip_unavailable" if upnp_available else "upnp_unavailable"
        return "unknown", "unknown", reason
    if gateway in SHARED_ADDRESS_SPACE:
        return "cgnat", "relay", "gateway_shared_address"
    if any(gateway in network for network in PRIVATE_NETWORKS):
        return "upstream_nat", "relay", "gateway_private_address"
    if not gateway.is_global or gateway.is_multicast:
        return "unknown", "unknown", "gateway_address_not_global"
    if observed is None:
        return "unknown", "unknown", "public_ip_unavailable"
    if gateway != observed:
        return "upstream_nat", "relay", "public_ip_mismatch"
    return "public_ipv4", "direct", "public_ipv4_candidate"


class NetworkDetector:
    """Read network evidence without opening ports or claiming verified inbound access."""

    def __init__(self, upnp_service: UPNPService, *, public_ip_urls: tuple[str, ...] = PUBLIC_IP_URLS):
        for url in public_ip_urls:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Public IP sources must be HTTPS URLs without credentials")
        self._upnp = upnp_service
        self._public_ip_urls = public_ip_urls

    async def detect(self) -> NetworkReport:
        observed, (gateway, available) = await asyncio.gather(self._public_ip(), self._gateway_ip())
        topology, mode, reason = _classify(observed, gateway, available)
        return NetworkReport(
            topology=topology,
            recommended_mode=mode,
            observed_public_ip=str(observed) if observed else None,
            gateway_external_ip=str(gateway) if gateway else None,
            upnp_available=available,
            checked_at=datetime.now(timezone.utc),
            reason_code=reason,
        )

    async def _gateway_ip(self) -> tuple[IPv4Address | None, bool]:
        try:
            async with asyncio.timeout(GATEWAY_TIMEOUT_SECONDS):
                value = await self._upnp.get_external_ip()
        except Exception:
            # Discovery/action failures are expected on networks without UPnP.
            return None, False
        return _ipv4(value), True

    async def _public_ip(self) -> IPv4Address | None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector, trust_env=False) as session:
            for url in self._public_ip_urls:
                try:
                    address = await self._read_public_ip(session, url)
                except (aiohttp.ClientError, TimeoutError, UnicodeDecodeError):
                    continue
                if address is not None:
                    return address
        return None

    @staticmethod
    async def _read_public_ip(session: aiohttp.ClientSession, url: str) -> IPv4Address | None:
        async with session.get(url, allow_redirects=False) as response:
            if response.status != 200:
                return None
            body = bytearray()
            async for chunk in response.content.iter_chunked(MAX_IP_RESPONSE_BYTES):
                body.extend(chunk)
                if len(body) > MAX_IP_RESPONSE_BYTES:
                    return None
            address = _ipv4(body.decode("ascii"))
            if address is None or not address.is_global or address.is_multicast:
                return None
            return address
