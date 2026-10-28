from ipaddress import IPv4Address
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, HttpUrl


def validate_device_url(value: HttpUrl) -> HttpUrl:
    if value.username or value.password or value.fragment:
        raise ValueError("Device URL must not contain credentials or a fragment")
    return value


DeviceURL = Annotated[HttpUrl, AfterValidator(validate_device_url)]


class GatewayTarget(BaseModel):
    device_url: DeviceURL = Field(description="UPnP device description XML URL, not the admin page")


class GatewayInfo(BaseModel):
    device_url: str
    host: str
    name: str = ""
    external_ip: str | None = None
    address_scope: Literal["public", "private", "shared", "unknown"] = "unknown"
    is_default: bool = False
    reachable: bool = True
    error: str | None = None


class GatewayMappingCreate(BaseModel):
    external_port: int = Field(ge=1, le=65535)
    internal_port: int = Field(ge=1, le=65535)
    protocol: Literal["TCP", "UDP"] = "TCP"
    local_ip: IPv4Address = Field(description="Service IP or the next router's WAN IPv4 address")
    description: str = Field(default="", max_length=256)
    lease_duration: int = Field(default=0, ge=0, le=4294967295)
    enabled: Literal[True] = True
