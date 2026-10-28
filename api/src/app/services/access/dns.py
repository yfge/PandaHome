"""Idempotent DDNS synchronization through the existing Aliyun service."""

import asyncio
import ipaddress

from ...schemas.domains import DomainRecordCreateRequest, DomainRecordUpdateRequest
from ..aliyun_dns import AliyunDNSService


class DnsConflict(RuntimeError):
    pass


class DnsSync:
    def __init__(self, factory=AliyunDNSService):
        self._factory = factory

    async def sync(self, row, public_host: str) -> str:
        if not row.domain:
            return "not_configured"
        await asyncio.to_thread(self._sync, row.domain, row.rr, public_host)
        return "updated"

    def _sync(self, domain: str, rr: str, public_host: str) -> None:
        service = self._factory()
        try:
            address = ipaddress.ip_address(public_host)
        except ValueError:
            record_type, value = "CNAME", public_host.rstrip(".").lower()
        else:
            record_type, value = ("A" if address.version == 4 else "AAAA"), str(address)
        if record_type == "CNAME" and rr == "@":
            raise DnsConflict("Use a subdomain when the relay public host is a DNS name.")
        records = [r for r in service.get_domain_records(domain) if r.RR == rr and r.Line == "default"]
        if record_type == "CNAME" and any(
            r.Type not in {"A", "CNAME", "AAAA", "RRSIG", "NSEC", "NSEC3"} for r in records
        ):
            raise DnsConflict(
                "A CNAME cannot share its hostname with other DNS records; choose a dedicated host record."
            )
        relevant = [
            r
            for r in records
            if r.Type in {record_type, "CNAME"} or (record_type == "CNAME" and r.Type in {"A", "AAAA"})
        ]
        if len(relevant) > 1:
            raise DnsConflict("Multiple DNS records match this hostname; choose a dedicated host record.")
        if relevant:
            record = relevant[0]
            if record.Status != "ENABLE":
                raise DnsConflict("The matching DNS record is disabled; enable it before publishing this service.")
            if record.Type == record_type and record.Value.rstrip(".").lower() == value:
                return
            if record.Locked:
                raise DnsConflict("The matching DNS record is locked; unlock it before changing the public endpoint.")
            service.update_domain_record(
                domain, record.RecordId, DomainRecordUpdateRequest(rr=rr, type=record_type, value=value)
            )
        else:
            service.add_domain_record(
                domain, DomainRecordCreateRequest(rr=rr, type=record_type, value=value, line="default")
            )
