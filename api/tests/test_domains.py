from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.routers.domains import get_dns_service
from src.app.schemas.domains import DomainRecord, DomainRecordWriteResponse, DomainSummary
from src.app.services.aliyun_dns import AliyunDNSError, AliyunDNSErrorCode


class StubDNSService:
    def __init__(self) -> None:
        self.domains: list[DomainSummary] = [
            DomainSummary(domain="example.com", id="d-123", status="ENABLE"),
        ]
        self.records: list[DomainRecord] = [
            DomainRecord(
                Status="ENABLE",
                RR="www",
                Line="default",
                Locked=False,
                Type="A",
                DomainName="example.com",
                Value="192.0.2.10",
                RecordId="r-1",
                TTL=600,
                CreateTimestamp=1_700_000_000,
                UpdateTimestamp=1_700_000_100,
                Priority=None,
                Weight=None,
            )
        ]
        self.add_response = DomainRecordWriteResponse(record_id="r-new", request_id="req-1")
        self.update_response = DomainRecordWriteResponse(record_id="r-1", request_id="req-2")

        self.raise_on_list_domains: Exception | None = None
        self.raise_on_list_records: Exception | None = None
        self.raise_on_add_record: Exception | None = None
        self.raise_on_update_record: Exception | None = None
        self.raise_on_delete_record: Exception | None = None

        self.add_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []
        self.delete_calls: list[str] = []

    def get_domains_list(self) -> list[DomainSummary]:
        if self.raise_on_list_domains:
            raise self.raise_on_list_domains
        return self.domains

    def get_domain_records(self, domain_name: str) -> list[DomainRecord]:
        if self.raise_on_list_records:
            raise self.raise_on_list_records
        return self.records

    def add_domain_record(self, domain_name: str, payload: Any) -> DomainRecordWriteResponse:
        self.add_calls.append({"domain_name": domain_name, "payload": payload.model_dump()})
        if self.raise_on_add_record:
            raise self.raise_on_add_record
        return self.add_response

    def update_domain_record(self, domain_name: str, record_id: str, payload: Any) -> DomainRecordWriteResponse:
        self.update_calls.append({"domain_name": domain_name, "record_id": record_id, "payload": payload.model_dump()})
        if self.raise_on_update_record:
            raise self.raise_on_update_record
        return self.update_response

    def delete_domain_record(self, record_id: str) -> None:
        self.delete_calls.append(record_id)
        if self.raise_on_delete_record:
            raise self.raise_on_delete_record


@pytest.fixture()
def stub_dns_service() -> StubDNSService:
    stub = StubDNSService()
    app.dependency_overrides[get_dns_service] = lambda: stub
    try:
        yield stub
    finally:
        app.dependency_overrides.pop(get_dns_service, None)


def test_domains_list_success(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.get("/api/domains/domains")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == [stub_dns_service.domains[0].model_dump()]


def test_domains_list_aliyun_error_mapped_to_502(client: TestClient, stub_dns_service: StubDNSService) -> None:
    stub_dns_service.raise_on_list_domains = AliyunDNSError(AliyunDNSErrorCode.REQUEST_FAILED, "Aliyun down")
    response = client.get("/api/domains/domains")
    assert response.status_code == 502
    assert response.json()["detail"] == "Aliyun down"


def test_domain_records_success(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.get("/api/domains/domains/example.com/records")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == [stub_dns_service.records[0].model_dump()]


def test_domain_records_aliyun_error_mapped_to_502(client: TestClient, stub_dns_service: StubDNSService) -> None:
    stub_dns_service.raise_on_list_records = AliyunDNSError(AliyunDNSErrorCode.NOT_FOUND, "not found")
    response = client.get("/api/domains/domains/example.com/records")
    assert response.status_code == 502
    assert response.json()["detail"] == "not found"


def test_domain_add_record_requires_body(client: TestClient) -> None:
    response = client.post("/api/domains/domains/example.com/records")
    assert response.status_code == 422


def test_domain_add_record_success(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.post(
        "/api/domains/domains/example.com/records",
        json={"rr": "test", "type": "A", "value": "192.0.2.20"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_dns_service.add_response.model_dump()
    assert stub_dns_service.add_calls == [
        {"domain_name": "example.com", "payload": {"rr": "test", "type": "A", "value": "192.0.2.20", "ttl": None, "line": None, "priority": None}}
    ]


def test_domain_update_record_requires_payload(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.put("/api/domains/domains/example.com/records/r-1", json={})
    assert response.status_code == 422


def test_domain_update_record_success(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.put(
        "/api/domains/domains/example.com/records/r-1",
        json={"value": "192.0.2.30"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_dns_service.update_response.model_dump()
    assert stub_dns_service.update_calls == [{"domain_name": "example.com", "record_id": "r-1", "payload": {"rr": None, "type": None, "value": "192.0.2.30", "ttl": None, "line": None, "priority": None}}]


def test_domain_delete_record_success(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.delete("/api/domains/domains/example.com/records/r-1")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert stub_dns_service.delete_calls == ["r-1"]


def test_domain_delete_record_legacy_path_still_works(client: TestClient, stub_dns_service: StubDNSService) -> None:
    response = client.delete("/api/domains/records/r-1")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert stub_dns_service.delete_calls == ["r-1"]
