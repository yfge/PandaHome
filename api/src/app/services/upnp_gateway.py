"""Request-scoped control of an explicitly selected IGD, independent of discovery."""

import asyncio
from contextlib import asynccontextmanager
from ipaddress import IPv4Address, ip_address, ip_network
from typing import Any
from urllib.parse import urlsplit

import aiohttp
from async_upnp_client.aiohttp import AiohttpSessionRequester
from async_upnp_client.client import UpnpDevice, UpnpService
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.exceptions import UpnpActionError, UpnpError
from async_upnp_client.search import async_search
from pydantic import TypeAdapter, ValidationError

from ..schemas.upnp_gateway import DeviceURL, GatewayInfo, GatewayMappingCreate

SERVICE_TYPES = (
    "urn:schemas-upnp-org:service:WANIPConnection:2",
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANPPPConnection:1",
)
DEVICE_URL_ADAPTER = TypeAdapter(DeviceURL)
MAX_MAPPINGS = 256
MAX_GATEWAYS = 16
HTTP_TIMEOUT_SECONDS = 5
OPERATION_TIMEOUT_SECONDS = 20
SSDP_SEARCH_SECONDS = 3
SSDP_TIMEOUT_SECONDS = 5


class GatewayError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def address_scope(value: str | None) -> str:
    try:
        address = ip_address(value or "")
    except ValueError:
        return "unknown"
    if not isinstance(address, IPv4Address) or address.is_unspecified or address.is_multicast:
        return "unknown"
    if address in ip_network("100.64.0.0/10"):
        return "shared"
    if any(address in ip_network(network) for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        return "private"
    return "public" if address.is_global else "unknown"


def find_wan_service(device: UpnpDevice) -> UpnpService:
    for service_type in SERVICE_TYPES:
        for service in device.all_services:
            if service.service_type == service_type:
                return service
    raise GatewayError("The selected device has no supported UPnP WAN service")


class GatewayClient:
    def __init__(self, device_url: str, device: UpnpDevice, service: UpnpService):
        self.device_url = device_url
        self.device = device
        self.service = service

    async def info(self, default_host: str | None = None) -> GatewayInfo:
        error = None
        external_ip = None
        try:
            result = await self.service.async_call_action("GetExternalIPAddress")
            external_ip = result.get("NewExternalIPAddress") or None
        except Exception:
            error = "The router's WAN address could not be read"
        host = urlsplit(self.device_url).hostname or ""
        return GatewayInfo(
            device_url=self.device_url, host=host, name=self.device.friendly_name or host,
            external_ip=external_ip, address_scope=address_scope(external_ip),
            is_default=host == default_host, error=error,
        )

    async def mappings(self) -> dict[str, Any]:
        if not self.service.has_action("GetGenericPortMappingEntry"):
            return {"mappings": [], "enumeration_supported": False, "complete": False}
        mappings = []
        for index in range(MAX_MAPPINGS):
            try:
                result = await self.service.async_call_action("GetGenericPortMappingEntry", NewPortMappingIndex=index)
            except UpnpActionError as exc:
                if exc.error_code in {713, 714}:
                    return {"mappings": mappings, "enumeration_supported": True, "complete": True}
                if index == 0 and exc.error_code == 401:
                    return {"mappings": [], "enumeration_supported": False, "complete": False}
                raise GatewayError("The selected router could not list its port mappings") from exc
            mappings.append({
                "external_port": result["NewExternalPort"], "internal_port": result["NewInternalPort"],
                "protocol": result["NewProtocol"], "internal_ip": result["NewInternalClient"],
                "enabled": result.get("NewEnabled", True), "description": result.get("NewPortMappingDescription", ""),
                "lease_duration": result.get("NewLeaseDuration", 0),
            })
        return {"mappings": mappings, "enumeration_supported": True, "complete": False}

    async def add_mapping(self, mapping: GatewayMappingCreate) -> dict[str, Any]:
        # A successful AddPortMapping can overwrite an existing rule. Check the
        # exact port/protocol independently of optional full-table enumeration.
        if not self.service.has_action("GetSpecificPortMappingEntry"):
            raise GatewayError("This router cannot check existing mappings; no mapping was changed")
        key = {"NewRemoteHost": "", "NewExternalPort": mapping.external_port, "NewProtocol": mapping.protocol}
        try:
            await self.service.async_call_action("GetSpecificPortMappingEntry", **key)
        except UpnpActionError as exc:
            if exc.error_code != 714:
                raise GatewayError("Unable to check whether this port is already mapped; no mapping was changed") from exc
        else:
            raise GatewayError("A mapping already exists for this port and protocol", 409)
        await self._mutate(
            "AddPortMapping", **key, NewInternalPort=mapping.internal_port,
            NewInternalClient=str(mapping.local_ip), NewEnabled=True,
            NewPortMappingDescription=mapping.description, NewLeaseDuration=mapping.lease_duration,
        )
        return {"status": "success", "device_url": self.device_url}

    async def delete_mapping(self, port: int, protocol: str) -> dict[str, Any]:
        await self._mutate("DeletePortMapping", NewRemoteHost="", NewExternalPort=port, NewProtocol=protocol)
        return {"status": "success", "device_url": self.device_url}

    async def _mutate(self, action: str, **params: Any) -> None:
        if not self.service.has_action(action):
            raise GatewayError(f"The selected router does not support {action}")
        try:
            await self.service.async_call_action(action, **params)
        except UpnpActionError as exc:
            status_code = {714: 404, 718: 409}.get(exc.error_code, 502)
            raise GatewayError(f"The selected router rejected {action} (UPnP {exc.error_code})", status_code) from exc


@asynccontextmanager
async def open_gateway(device_url: str):
    """Never change the application's default IGD or share a target/cache."""
    try:
        async with asyncio.timeout(OPERATION_TIMEOUT_SECONDS), aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS), trust_env=False,
        ) as session:
            factory = UpnpFactory(AiohttpSessionRequester(session, timeout=HTTP_TIMEOUT_SECONDS), non_strict=True)
            try:
                device = await factory.async_create_device(device_url)
                service = find_wan_service(device)
            except GatewayError:
                raise
            except Exception as exc:
                raise GatewayError("Could not load the selected UPnP device; check its description URL and access policy") from exc
            yield GatewayClient(device_url, device, service)
    except GatewayError:
        raise
    except TimeoutError as exc:
        raise GatewayError("The selected router timed out; it may be unreachable or may have applied the request", 504) from exc
    except (UpnpError, aiohttp.ClientError, OSError) as exc:
        raise GatewayError("UPnP communication with the selected router failed; check its address and access policy") from exc


async def discover_gateways(default_service: Any, refresh: bool = False) -> dict[str, Any]:
    locations: set[str] = set()

    async def discovered(headers):
        location = headers.get("location") or headers.get("LOCATION")
        if location:
            try:
                locations.add(str(DEVICE_URL_ADAPTER.validate_python(location)))
            except ValidationError:
                pass

    for headers in list(getattr(default_service, "devices", [])):
        await discovered(headers)
    discovery_error = None
    if refresh:
        source = getattr(default_service, "interface_ip", None)
        try:
            async with asyncio.timeout(SSDP_TIMEOUT_SECONDS):
                await async_search(
                    discovered, timeout=SSDP_SEARCH_SECONDS,
                    search_target="urn:schemas-upnp-org:device:InternetGatewayDevice:1",
                    **({"source": (source, 0)} if source else {}),
                )
        except Exception:
            discovery_error = "Local discovery failed; a device description URL can still be entered manually"
    default_host = (getattr(default_service, "gateway_info", None) or {}).get("ip")

    async def inspect(location: str) -> GatewayInfo:
        try:
            async with open_gateway(location) as gateway:
                return await gateway.info(default_host)
        except GatewayError as exc:
            host = urlsplit(location).hostname or ""
            return GatewayInfo(
                device_url=location, host=host, is_default=host == default_host,
                reachable=False, error=str(exc),
            )

    # Bound work when a network advertises an unexpectedly large device list.
    gateways = await asyncio.gather(*(inspect(location) for location in sorted(locations)[:MAX_GATEWAYS]))
    return {"gateways": [gateway.model_dump() for gateway in gateways], "discovery_error": discovery_error}
