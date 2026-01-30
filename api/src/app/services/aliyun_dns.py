from __future__ import annotations

import json
from enum import Enum

from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DeleteDomainRecordRequest import DeleteDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainsRequest import DescribeDomainsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest

from ..config import settings
from ..schemas.domains import DomainRecord, DomainRecordCreateRequest, DomainRecordUpdateRequest, DomainRecordWriteResponse, DomainSummary
from .logger import logger


class AliyunDNSErrorCode(str, Enum):
    CONFIG_MISSING = "config_missing"
    AUTH_FAILED = "auth_failed"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    REQUEST_FAILED = "request_failed"


class AliyunDNSError(RuntimeError):
    def __init__(self, code: AliyunDNSErrorCode, message: str, *, provider_code: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider_code = provider_code


def _extract_provider_code(exc: Exception) -> str | None:
    for attr in ("error_code", "code", "ErrorCode"):
        value = getattr(exc, attr, None)
        if isinstance(value, str) and value:
            return value
    getter = getattr(exc, "get_error_code", None)
    if callable(getter):
        try:
            value = getter()
            if isinstance(value, str) and value:
                return value
        except Exception:
            return None
    return None


def _friendly_message(exc: Exception) -> tuple[AliyunDNSErrorCode, str]:
    provider_code = (_extract_provider_code(exc) or "").lower()
    raw_message = str(exc)

    if any(token in provider_code for token in ("invalidaccesskey", "signaturedoesnotmatch", "forbidden")):
        return AliyunDNSErrorCode.AUTH_FAILED, "Aliyun credentials are invalid or do not have DNS permissions."

    if any(token in provider_code for token in ("domainnotfound", "recordnotfound", "invaliddomainname")):
        return AliyunDNSErrorCode.NOT_FOUND, "Requested domain/record was not found in Aliyun DNS."

    if any(token in provider_code for token in ("throttling", "ratelimit", "limit")):
        return AliyunDNSErrorCode.RATE_LIMITED, "Aliyun DNS API rate limit reached. Please retry later."

    return AliyunDNSErrorCode.REQUEST_FAILED, f"Aliyun DNS API request failed: {raw_message}"

class AliyunDNSService:
    def __init__(self):
        self._config_error: AliyunDNSError | None = None
        self.client: AcsClient | None = None

        if not settings.ALIYUN_ACCESS_KEY_ID or not settings.ALIYUN_ACCESS_KEY_SECRET:
            self._config_error = AliyunDNSError(
                AliyunDNSErrorCode.CONFIG_MISSING,
                "Aliyun credentials are not configured. Set ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET.",
            )
            return

        self.client = AcsClient(
            settings.ALIYUN_ACCESS_KEY_ID,
            settings.ALIYUN_ACCESS_KEY_SECRET,
            settings.ALIYUN_REGION_ID,
        )

    def _require_client(self) -> AcsClient:
        if self._config_error is not None:
            raise self._config_error
        if self.client is None:
            raise AliyunDNSError(AliyunDNSErrorCode.CONFIG_MISSING, "Aliyun DNS client is not configured.")
        return self.client

    def get_domains_list(self) -> list[DomainSummary]:
        """获取域名列表"""
        request = DescribeDomainsRequest()
        request.set_accept_format('json')

        try:
            logger.info("AliyunDNS: listing domains")
            response = self._require_client().do_action_with_exception(request)
            response_data = json.loads(response)

            domains: list[DomainSummary] = []
            for domain in response_data.get("Domains", {}).get("Domain", []):
                domains.append(
                    DomainSummary(
                        domain=domain["DomainName"],
                        id=domain["DomainId"],
                        status=domain.get("DomainStatus") or domain.get("VersionName") or "unknown",
                    )
                )

            logger.info(f"AliyunDNS: listed domains count={len(domains)}")
            return domains
        except (ClientException, ServerException) as e:
            code, message = _friendly_message(e)
            provider_code = _extract_provider_code(e)
            logger.error(f"AliyunDNS: list domains failed code={provider_code} error={e}")
            raise AliyunDNSError(code, message, provider_code=provider_code) from e
        except Exception as e:
            logger.error(f"处理域名列表时发生错误: {str(e)}")
            raise

    def get_domain_records(self, domain_name: str) -> list[DomainRecord]:
        """获取域名解析记录"""
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)

        try:
            logger.info(f"AliyunDNS: listing records domain={domain_name}")
            response = self._require_client().do_action_with_exception(request)
            response_data = json.loads(response)
            record_payload = response_data.get("DomainRecords", {}).get("Record") or []
            if isinstance(record_payload, dict):
                records_raw = [record_payload]
            else:
                records_raw = list(record_payload)

            records: list[DomainRecord] = [DomainRecord.model_validate(item) for item in records_raw]
            logger.info(f"AliyunDNS: listed records domain={domain_name} count={len(records)}")
            return records
        except (ClientException, ServerException) as e:
            code, message = _friendly_message(e)
            provider_code = _extract_provider_code(e)
            logger.error(f"AliyunDNS: list records failed domain={domain_name} code={provider_code} error={e}")
            raise AliyunDNSError(code, message, provider_code=provider_code) from e

    def validate_domain(self, domain_name: str) -> bool:
        """验证域名是否存在"""
        domains = self.get_domains_list()
        return any(domain.domain == domain_name for domain in domains)

    def validate_record(self, domain_name: str, rr: str) -> bool:
        """验证解析记录是否已存在"""
        records = self.get_domain_records(domain_name)
        return any(record.RR == rr for record in records)

    def add_domain_record(self, domain_name: str, payload: DomainRecordCreateRequest) -> DomainRecordWriteResponse:
        """添加域名解析记录"""
        request = AddDomainRecordRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)
        request.set_RR(payload.rr)
        request.set_Type(payload.type)
        request.set_Value(payload.value)
        if payload.ttl is not None:
            request.set_TTL(payload.ttl)
        if payload.line is not None:
            request.set_Line(payload.line)
        if payload.priority is not None:
            request.set_Priority(payload.priority)

        try:
            logger.info(f"AliyunDNS: add record domain={domain_name} rr={payload.rr} type={payload.type}")
            response = self._require_client().do_action_with_exception(request)
            response_data = json.loads(response)
            return DomainRecordWriteResponse(
                record_id=str(response_data.get("RecordId", "")),
                request_id=response_data.get("RequestId"),
            )
        except (ClientException, ServerException) as e:
            code, message = _friendly_message(e)
            provider_code = _extract_provider_code(e)
            logger.error(f"AliyunDNS: add record failed domain={domain_name} code={provider_code} error={e}")
            raise AliyunDNSError(code, message, provider_code=provider_code) from e

    def update_domain_record(
        self,
        domain_name: str,
        record_id: str,
        payload: DomainRecordUpdateRequest,
    ) -> DomainRecordWriteResponse:
        request = UpdateDomainRecordRequest()
        request.set_accept_format("json")
        request.set_RecordId(record_id)
        if payload.rr is not None:
            request.set_RR(payload.rr)
        if payload.type is not None:
            request.set_Type(payload.type)
        if payload.value is not None:
            request.set_Value(payload.value)
        if payload.ttl is not None:
            request.set_TTL(payload.ttl)
        if payload.line is not None:
            request.set_Line(payload.line)
        if payload.priority is not None:
            request.set_Priority(payload.priority)

        try:
            logger.info(f"AliyunDNS: update record domain={domain_name} record_id={record_id}")
            response = self._require_client().do_action_with_exception(request)
            response_data = json.loads(response)
            return DomainRecordWriteResponse(
                record_id=str(response_data.get("RecordId", record_id)),
                request_id=response_data.get("RequestId"),
            )
        except (ClientException, ServerException) as e:
            code, message = _friendly_message(e)
            provider_code = _extract_provider_code(e)
            logger.error(
                f"AliyunDNS: update record failed domain={domain_name} record_id={record_id} code={provider_code} error={e}"
            )
            raise AliyunDNSError(code, message, provider_code=provider_code) from e

    def delete_domain_record(self, record_id: str) -> None:
        """删除域名解析记录"""
        request = DeleteDomainRecordRequest()
        request.set_accept_format('json')
        request.set_RecordId(record_id)

        try:
            self._require_client().do_action_with_exception(request)
            logger.info(f"AliyunDNS: deleted record_id={record_id}")
        except (ClientException, ServerException) as e:
            code, message = _friendly_message(e)
            provider_code = _extract_provider_code(e)
            logger.error(f"AliyunDNS: delete record failed record_id={record_id} code={provider_code} error={e}")
            raise AliyunDNSError(code, message, provider_code=provider_code) from e
        except Exception as e:
            logger.error(f"AliyunDNS: delete record failed record_id={record_id} error={e}")
            raise
