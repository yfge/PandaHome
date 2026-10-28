from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from async_upnp_client.exceptions import UpnpActionError

from ...models.published_service import PublishedService
from ..upnp import UPNPService

MISSING_MAPPING_CODES = {713, 714}


class MappingConflict(RuntimeError):
    """The requested public port belongs to a different mapping."""


def _key(spec: dict[str, Any]) -> dict[str, Any]:
    return {"NewRemoteHost": "", "NewExternalPort": spec["external_port"], "NewProtocol": spec["protocol"]}


def _same_mapping(existing: Mapping[str, Any], spec: dict[str, Any]) -> bool:
    try:
        return (
            existing.get("NewPortMappingDescription") == spec["description"]
            and existing.get("NewInternalClient") == spec["local_ip"]
            and int(existing.get("NewInternalPort")) == spec["internal_port"]
        )
    except (TypeError, ValueError):
        return False


class ManagedMappings:
    """Reconcile owned mappings using fresh, specific lookups instead of enumeration."""

    def __init__(self, upnp: UPNPService):
        self._upnp = upnp
        self._lock = asyncio.Lock()

    @staticmethod
    def spec(row: PublishedService) -> dict[str, Any]:
        if not row.owner_token:
            raise ValueError("A persisted mapping owner token is required")
        return {
            "external_port": row.public_port,
            "internal_port": row.local_port,
            "local_ip": row.local_ip,
            "protocol": row.protocol,
            "description": f"PandaHome:{row.owner_token}",
        }

    async def ensure(self, row: PublishedService) -> dict[str, Any]:
        spec = self.spec(row)
        async with self._lock:
            service = await self._upnp.gateway_service()
            existing = await self._read(service, spec)
            if existing is not None and not _same_mapping(existing, spec):
                raise MappingConflict("The public port is already used by another mapping")
            arguments = {
                **_key(spec),
                "NewInternalPort": spec["internal_port"],
                "NewInternalClient": spec["local_ip"],
                "NewEnabled": True,
                "NewPortMappingDescription": spec["description"],
                "NewLeaseDuration": row.lease_duration,
            }
            try:
                await service.async_call_action("AddPortMapping", **arguments)
            except UpnpActionError as exc:
                if exc.error_code != 725 or row.lease_duration == 0:
                    raise
                arguments["NewLeaseDuration"] = 0
                await service.async_call_action("AddPortMapping", **arguments)
            self._upnp.invalidate_mappings_cache()
        return spec

    async def remove(self, spec: dict[str, Any]) -> None:
        description = spec.get("description")
        if not isinstance(description, str) or not description.startswith("PandaHome:") or description == "PandaHome:":
            return
        async with self._lock:
            service = await self._upnp.gateway_service()
            existing = await self._read(service, spec)
            if existing is None or not _same_mapping(existing, spec):
                return
            try:
                await service.async_call_action("DeletePortMapping", **_key(spec))
            except UpnpActionError as exc:
                if exc.error_code not in MISSING_MAPPING_CODES:
                    raise
            self._upnp.invalidate_mappings_cache()

    @staticmethod
    async def _read(service, spec: dict[str, Any]) -> Mapping[str, Any] | None:
        try:
            result = await service.async_call_action("GetSpecificPortMappingEntry", **_key(spec))
        except UpnpActionError as exc:
            if exc.error_code in MISSING_MAPPING_CODES:
                return None
            raise
        if not isinstance(result, Mapping):
            raise MappingConflict("Could not verify existing port mapping ownership")
        return result
