"""Explicit IGD selection for per-layer NAT mapping; existing routes stay compatible."""

from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from ..auth.auth import require_role
from ..models.db_models import User
from ..models.response import Response
from ..models.user import UserRole
from ..schemas.upnp_gateway import DeviceURL, GatewayMappingCreate, GatewayTarget
from ..services.upnp_gateway import GatewayClient, GatewayError, discover_gateways, open_gateway


async def active_admin(user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


router = APIRouter(prefix="/gateways", tags=["upnp"], dependencies=[Depends(active_admin)])


async def selected_gateway(
    device_url: Annotated[DeviceURL, Query(description="UPnP device description XML URL")],
) -> AsyncIterator[GatewayClient]:
    try:
        async with open_gateway(str(device_url)) as gateway:
            yield gateway
    except GatewayError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("")
async def gateways(request: Request, refresh: bool = False):
    """Inspect discovered IGDs; refresh optionally runs a local SSDP search (read-only)."""
    result = await discover_gateways(request.app.state.upnp_service, refresh)
    return Response.success(data=result)


@router.post("/inspect")
async def inspect_gateway(target: GatewayTarget, request: Request):
    """Inspect an upstream IGD by its reachable description URL, without mapping a port."""
    try:
        async with open_gateway(str(target.device_url)) as gateway:
            default_host = (getattr(request.app.state.upnp_service, "gateway_info", None) or {}).get("ip")
            return Response.success(data=(await gateway.info(default_host)).model_dump())
    except GatewayError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/mappings")
async def mappings(gateway: GatewayClient = Depends(selected_gateway)):
    """List only the explicitly selected router's mappings; no default-router fallback."""
    return Response.success(data=await gateway.mappings())


@router.post("/mappings")
async def add_mapping(mapping: GatewayMappingCreate, gateway: GatewayClient = Depends(selected_gateway)):
    """Map to a service IPv4 or, on an outer router, the next router's WAN IPv4."""
    return Response.success(data=await gateway.add_mapping(mapping))


@router.delete("/mappings/{external_port}")
async def delete_mapping(
    external_port: Annotated[int, Path(ge=1, le=65535)],
    protocol: Literal["TCP", "UDP"] = "TCP",
    gateway: GatewayClient = Depends(selected_gateway),
):
    """Delete the specified port/protocol on the explicitly selected IGD only."""
    return Response.success(data=await gateway.delete_mapping(external_port, protocol))
