from fastapi import APIRouter, HTTPException
from ..services.upnp import UPNPService
from ..models.response import Response
from ..models.upnp import PortMapping

router = APIRouter(prefix="/api/upnp", tags=["upnp"])
upnp_service = UPNPService()

@router.get("/status")
async def get_status():
    """获取UPnP服务状态"""
    try:
        return Response.success(data=upnp_service.get_status())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mappings")
async def get_port_mappings():
    """获取所有端口映射"""
    try:
        return Response.success(data=upnp_service.get_port_mappings())
    except Exception as e:
        if "UPnP服务未初始化" in str(e):
            raise HTTPException(status_code=503, detail="UPnP服务不可用")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mappings")
async def add_port_mapping(mapping: PortMapping):
    """添加端口映射"""
    try:
        return Response.success(data=upnp_service.add_port_mapping(
            external_port=mapping.external_port,
            internal_port=mapping.internal_port,
            local_ip=mapping.local_ip,
            description=mapping.description,
            lease_duration=mapping.lease_duration,
            protocol=mapping.protocol
        ))
    except Exception as e:
        if "UPnP服务未初始化" in str(e):
            raise HTTPException(status_code=503, detail="UPnP服务不可用")
        if "端口不可用" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        if "映射已存在" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/mappings/{external_port}")
async def delete_port_mapping(external_port: int, protocol: str = "TCP"):
    """删除端口映射"""
    try:
        return await upnp_service.delete_port_mapping(external_port, protocol)
    except Exception as e:
        if "UPnP服务未初始化" in str(e):
            raise HTTPException(status_code=503, detail="UPnP服务不可用")
        raise HTTPException(status_code=500, detail=str(e)) 