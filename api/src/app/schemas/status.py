from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ServiceState = Literal["running", "stopped", "error"]


class CpuStatus(BaseModel):
    usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    cores: int = Field(..., ge=1, description="Logical CPU cores")


class MemoryStatus(BaseModel):
    total: int = Field(..., ge=0, description="Total bytes")
    used: int = Field(..., ge=0, description="Used bytes")
    free: int = Field(..., ge=0, description="Free/available bytes")


class DiskStatus(BaseModel):
    total: int = Field(..., ge=0, description="Total bytes")
    used: int = Field(..., ge=0, description="Used bytes")
    free: int = Field(..., ge=0, description="Free bytes")


class ServiceStatus(BaseModel):
    name: str
    status: ServiceState


class ServerStatus(BaseModel):
    cpu: CpuStatus
    memory: MemoryStatus
    disk: DiskStatus
    uptime: int = Field(..., ge=0, description="Seconds since system boot")
    timestamp: int = Field(..., ge=0, description="Unix timestamp")
    services: list[ServiceStatus]
