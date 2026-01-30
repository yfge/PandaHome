from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.domains import DomainRecordCreateRequest, DomainRecordUpdateRequest
from ..services.aliyun_dns import AliyunDNSError, AliyunDNSService
from ..models.response import Response

router = APIRouter(prefix="/api/domains", tags=["domains"])


def get_dns_service() -> AliyunDNSService:
    return AliyunDNSService()


@router.get("/domains")
async def get_domains(dns_service: AliyunDNSService = Depends(get_dns_service)):
    """获取域名列表"""
    try:
        domains = dns_service.get_domains_list()
        return Response.success(data=domains)
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.get("/domains/{domain_name}/records")
async def get_domain_records(domain_name: str, dns_service: AliyunDNSService = Depends(get_dns_service)):
    """获取指定域名的解析记录"""
    try:
        records = dns_service.get_domain_records(domain_name)
        return Response.success(data=records)
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.post("/domains/{domain_name}/records")
async def add_domain_record(
    domain_name: str,
    payload: DomainRecordCreateRequest,
    dns_service: AliyunDNSService = Depends(get_dns_service),
):
    """添加域名解析记录"""
    try:
        record = dns_service.add_domain_record(domain_name, payload)
        return Response.success(data=record)
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.put("/domains/{domain_name}/records/{record_id}")
async def update_domain_record(
    domain_name: str,
    record_id: str,
    payload: DomainRecordUpdateRequest,
    dns_service: AliyunDNSService = Depends(get_dns_service),
):
    """更新域名解析记录"""
    try:
        record = dns_service.update_domain_record(domain_name, record_id, payload)
        return Response.success(data=record)
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.delete("/domains/{domain_name}/records/{record_id}")
async def delete_domain_record(domain_name: str, record_id: str, dns_service: AliyunDNSService = Depends(get_dns_service)):
    """删除域名解析记录"""
    try:
        dns_service.delete_domain_record(record_id)
        return Response.success()
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete("/records/{record_id}")
async def delete_domain_record_legacy(
    record_id: str,
    dns_service: AliyunDNSService = Depends(get_dns_service),
):
    """删除域名解析记录（兼容旧路径）"""
    try:
        dns_service.delete_domain_record(record_id)
        return Response.success()
    except AliyunDNSError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
