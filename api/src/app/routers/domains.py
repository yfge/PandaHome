from fastapi import APIRouter, Depends, HTTPException
from ..services.aliyun_dns import AliyunDNSService
from ..models.response import Response

router = APIRouter(prefix="/api/domains", tags=["domains"])

@router.get("/domains")
async def get_domains():
    """获取域名列表"""
    try:
        dns_service = AliyunDNSService()
        domains = dns_service.get_domains_list()
        return Response.success(data=domains)
    except Exception as e:
        return Response.error(message=str(e))

@router.get("/domains/{domain_name}/records")
async def get_domain_records(domain_name: str):
    """获取指定域名的解析记录"""
    try:
        dns_service = AliyunDNSService()
        records = dns_service.get_domain_records(domain_name)
        return Response.success(data=records)
    except Exception as e:
        return Response.error(message=str(e))

@router.post("/domains/{domain_name}/records")
async def add_domain_record(domain_name: str, rr: str, value: str):
    """添加域名解析记录"""
    try:
        dns_service = AliyunDNSService()
        record = dns_service.add_domain_record(domain_name, rr, value)
        return Response.success(data=record)
    except Exception as e:
        return Response.error(message=str(e))

@router.delete("/records/{record_id}")
async def delete_domain_record(record_id: str):
    """删除域名解析记录"""
    try:
        dns_service = AliyunDNSService()
        dns_service.delete_domain_record(record_id)
        return Response.success()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 