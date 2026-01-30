from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.services.upnp import UPNPErrorCode, UPNPServiceError


class StubUPNPService:
    def __init__(self) -> None:
        self.status_payload: dict[str, Any] = {"status": "available"}
        self.mappings_payload: dict[str, Any] = {
            "status": "success",
            "mappings": [],
            "connection_info": {},
        }
        self.add_result: dict[str, Any] = {"status": "success"}
        self.delete_result: dict[str, Any] = {"status": "success"}

        self.raise_on_status: Exception | None = None
        self.raise_on_get_mappings: Exception | None = None
        self.raise_on_add: Exception | None = None
        self.raise_on_delete: Exception | None = None

        self.add_calls: list[dict[str, Any]] = []
        self.delete_calls: list[dict[str, Any]] = []

    def get_status(self) -> dict[str, Any]:
        if self.raise_on_status:
            raise self.raise_on_status
        return self.status_payload

    async def get_port_mappings(self) -> dict[str, Any]:
        if self.raise_on_get_mappings:
            raise self.raise_on_get_mappings
        return self.mappings_payload

    async def add_port_mapping(
        self,
        *,
        external_port: int,
        internal_port: int,
        protocol: str,
        local_ip: str,
        description: str = "",
        lease_duration: int = 0,
    ) -> dict[str, Any]:
        self.add_calls.append(
            {
                "external_port": external_port,
                "internal_port": internal_port,
                "protocol": protocol,
                "local_ip": local_ip,
                "description": description,
                "lease_duration": lease_duration,
            }
        )

        if self.raise_on_add:
            raise self.raise_on_add
        return self.add_result

    async def delete_port_mapping(self, external_port: int, protocol: str = "TCP") -> dict[str, Any]:
        self.delete_calls.append({"external_port": external_port, "protocol": protocol})

        if self.raise_on_delete:
            raise self.raise_on_delete
        return self.delete_result


@pytest.fixture()
def stub_upnp_service() -> StubUPNPService:
    original = getattr(app.state, "upnp_service", None)
    stub = StubUPNPService()
    app.state.upnp_service = stub
    try:
        yield stub
    finally:
        app.state.upnp_service = original


def test_upnp_status_success(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.status_payload = {"status": "available", "devices": []}
    response = client.get("/api/upnp/status")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_upnp_service.status_payload


def test_upnp_status_failure_returns_500(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.raise_on_status = RuntimeError("boom")
    response = client.get("/api/upnp/status")
    assert response.status_code == 500
    assert response.json()["detail"] == "boom"


def test_upnp_mappings_success(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.mappings_payload = {
        "status": "success",
        "mappings": [
            {
                "external_port": 8080,
                "internal_port": 80,
                "protocol": "TCP",
                "internal_ip": "192.168.1.10",
                "enabled": True,
                "description": "web",
                "lease_duration": 0,
            }
        ],
        "connection_info": {"external_ip": "203.0.113.10"},
    }
    response = client.get("/api/upnp/mappings")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_upnp_service.mappings_payload


def test_upnp_mappings_unavailable_returns_503(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.raise_on_get_mappings = UPNPServiceError(UPNPErrorCode.UNAVAILABLE, "UPnP服务不可用")
    response = client.get("/api/upnp/mappings")
    assert response.status_code == 503
    assert response.json()["detail"] == "UPnP服务不可用"


def test_upnp_add_mapping_success(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.add_result = {"status": "success", "message": "added"}
    response = client.post(
        "/api/upnp/mappings",
        json={
            "external_port": 8080,
            "internal_port": 80,
            "protocol": "TCP",
            "local_ip": "192.168.1.10",
            "description": "web",
            "enabled": True,
            "lease_duration": 0,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_upnp_service.add_result
    assert stub_upnp_service.add_calls == [
        {
            "external_port": 8080,
            "internal_port": 80,
            "protocol": "TCP",
            "local_ip": "192.168.1.10",
            "description": "web",
            "lease_duration": 0,
        }
    ]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (UPNPServiceError(UPNPErrorCode.UNAVAILABLE, "UPnP服务不可用"), 503),
        (UPNPServiceError(UPNPErrorCode.INVALID_PORT, "端口不可用"), 400),
        (UPNPServiceError(UPNPErrorCode.INVALID_PROTOCOL, "协议不可用"), 400),
        (UPNPServiceError(UPNPErrorCode.MAPPING_EXISTS, "映射已存在"), 409),
        (UPNPServiceError(UPNPErrorCode.ACTION_FAILED, "内部错误"), 500),
    ],
)
def test_upnp_add_mapping_failure_codes(
    client: TestClient,
    stub_upnp_service: StubUPNPService,
    error: UPNPServiceError,
    expected_status: int,
) -> None:
    stub_upnp_service.raise_on_add = error
    response = client.post(
        "/api/upnp/mappings",
        json={
            "external_port": 8080,
            "internal_port": 80,
            "protocol": "TCP",
            "local_ip": "192.168.1.10",
            "description": "web",
            "enabled": True,
            "lease_duration": 0,
        },
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == error.message


def test_upnp_delete_mapping_success(client: TestClient, stub_upnp_service: StubUPNPService) -> None:
    stub_upnp_service.delete_result = {"status": "success", "message": "deleted"}
    response = client.delete("/api/upnp/mappings/8080?protocol=TCP")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"] == stub_upnp_service.delete_result
    assert stub_upnp_service.delete_calls == [{"external_port": 8080, "protocol": "TCP"}]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (UPNPServiceError(UPNPErrorCode.UNAVAILABLE, "UPnP服务不可用"), 503),
        (UPNPServiceError(UPNPErrorCode.INVALID_PORT, "端口不可用"), 400),
        (UPNPServiceError(UPNPErrorCode.INVALID_PROTOCOL, "协议不可用"), 400),
        (UPNPServiceError(UPNPErrorCode.MAPPING_NOT_FOUND, "端口映射不存在"), 404),
        (UPNPServiceError(UPNPErrorCode.ACTION_FAILED, "内部错误"), 500),
    ],
)
def test_upnp_delete_mapping_failure_codes(
    client: TestClient,
    stub_upnp_service: StubUPNPService,
    error: UPNPServiceError,
    expected_status: int,
) -> None:
    stub_upnp_service.raise_on_delete = error
    response = client.delete("/api/upnp/mappings/8080?protocol=TCP")
    assert response.status_code == expected_status
    assert response.json()["detail"] == error.message
