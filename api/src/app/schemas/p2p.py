"""P2P entries carry TCP application streams over frp's XTCP tunnel."""

import ipaddress
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class P2PServiceConfig(BaseModel):
    """A TCP service; UDP applications require a separate transport implementation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    local_ip: str
    local_port: int = Field(ge=1, le=65535)
    enabled: bool = True
    fallback_enabled: bool = True

    @field_validator("local_ip")
    @classmethod
    def validate_local_ip(cls, value: str) -> str:
        address = ipaddress.IPv4Address(value)
        if address.is_multicast or address.is_unspecified or address.is_reserved or int(address) == 0xFFFFFFFF:
            raise ValueError("Enter a unicast IPv4 address for the TCP service.")
        return str(address)


class P2PServiceView(P2PServiceConfig):
    id: int
    status: Literal["disabled", "needs_setup", "awaiting_connection", "error"]
    reason_code: str
    connection_type: Literal["unknown"] = "unknown"
