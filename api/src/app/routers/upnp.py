from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..services.upnp import UPNPErrorCode, UPNPService, UPNPServiceError
from ..models.response import Response
from ..models.upnp import PortMapping

router = APIRouter(prefix="/api/upnp", tags=["upnp"])


def get_upnp_service(request: Request) -> UPNPService:
    return request.app.state.upnp_service

@router.get("/status")
async def get_status(upnp_service: UPNPService = Depends(get_upnp_service)):
    """获取UPnP服务状态"""
    try:
        return Response.success(data=upnp_service.get_status())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mappings")
async def get_port_mappings(upnp_service: UPNPService = Depends(get_upnp_service)):
    """获取所有端口映射"""
    try:
        return Response.success(data=await upnp_service.get_port_mappings())
    except UPNPServiceError as e:
        if e.code == UPNPErrorCode.UNAVAILABLE:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)

@router.post("/mappings")
async def add_port_mapping(mapping: PortMapping, upnp_service: UPNPService = Depends(get_upnp_service)):
    """添加端口映射"""
    try:
        return Response.success(
            data=await upnp_service.add_port_mapping(
                external_port=mapping.external_port,
                internal_port=mapping.internal_port,
                local_ip=mapping.local_ip,
                description=mapping.description,
                lease_duration=mapping.lease_duration,
                protocol=mapping.protocol,
            )
        )
    except UPNPServiceError as e:
        if e.code == UPNPErrorCode.UNAVAILABLE:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
        if e.code in {
            UPNPErrorCode.INVALID_PORT,
            UPNPErrorCode.INVALID_PROTOCOL,
            UPNPErrorCode.INVALID_IP,
            UPNPErrorCode.INVALID_LEASE_DURATION,
        }:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
        if e.code == UPNPErrorCode.MAPPING_EXISTS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)

@router.delete("/mappings/{external_port}")
async def delete_port_mapping(
    external_port: int,
    protocol: str = "TCP",
    upnp_service: UPNPService = Depends(get_upnp_service),
):
    """删除端口映射"""
    try:
        return Response.success(data=await upnp_service.delete_port_mapping(external_port, protocol))
    except UPNPServiceError as e:
        if e.code == UPNPErrorCode.UNAVAILABLE:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
        if e.code in {
            UPNPErrorCode.INVALID_PORT,
            UPNPErrorCode.INVALID_PROTOCOL,
            UPNPErrorCode.INVALID_IP,
            UPNPErrorCode.INVALID_LEASE_DURATION,
        }:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
        if e.code == UPNPErrorCode.MAPPING_NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
