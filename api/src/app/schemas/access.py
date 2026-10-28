from __future__ import annotations

import ipaddress
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    local_ip: str
    local_port: int = Field(ge=1, le=65535)
    public_port: int = Field(ge=1, le=65535)
    protocol: Literal["TCP", "UDP"] = "TCP"
    mode: Literal["auto", "direct", "relay"] = "auto"
    domain: str = Field(default="", max_length=253)
    rr: str = Field(default="@", min_length=1, max_length=253)
    enabled: bool = True
    lease_duration: int = Field(default=3600, ge=0, le=604800)

    @field_validator("local_ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        address = ipaddress.IPv4Address(value)
        if address.is_multicast or address.is_unspecified or address.is_reserved or int(address) == 0xFFFFFFFF:
            raise ValueError("Enter a unicast IPv4 address for the service host.")
        return str(address)

    @field_validator("domain", "rr")
    @classmethod
    def validate_dns_name(cls, value: str) -> str:
        if value in {"", "@"}:
            return value
        value = value.rstrip(".").encode("idna").decode("ascii").lower()
        if len(value) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in value.split(".")
        ):
            raise ValueError("Enter a DNS name without a scheme, path or port.")
        return value

    @model_validator(mode="after")
    def validate_target(self) -> ServiceConfig:
        if 0 < self.lease_duration < 60:
            raise ValueError("Mapping leases must be zero (permanent) or at least 60 seconds.")
        if self.domain == "@":
            raise ValueError("Domain must be a DNS zone, e.g. example.com.")
        if self.mode != "relay" and ipaddress.IPv4Address(self.local_ip).is_loopback:
            raise ValueError("Use the server's LAN IPv4 address for automatic or direct access.")
        if self.domain and len(self.hostname) > 253:
            raise ValueError("The complete public hostname is too long.")
        return self

    @property
    def hostname(self) -> str:
        return self.domain if self.rr == "@" else f"{self.rr}.{self.domain}"


class ServiceView(ServiceConfig):
    id: int
    status: Literal["pending", "healthy", "degraded", "error", "needs_setup", "disabled"] = "pending"
    active_mode: Literal["direct", "relay"] | None = None
    public_endpoint: str | None = None
    dns_status: str = "pending"
    reason_code: str | None = "checking"
    last_error: str | None = None
    last_checked: datetime | None = None
    external_verified: bool = False
    failure_count: int = 0

    model_config = ConfigDict(from_attributes=True, extra="ignore")
