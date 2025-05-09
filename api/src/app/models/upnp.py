from pydantic import BaseModel, Field
from typing import Literal

class PortMapping(BaseModel):
    """端口映射模型"""
    external_port: int = Field(..., description="外部端口", ge=1, le=65535)
    internal_port: int = Field(..., description="内部端口", ge=1, le=65535)
    protocol: Literal["TCP", "UDP"] = Field("TCP", description="协议类型")
    local_ip: str = Field("", description="本地IP地址")
    description: str = Field("", description="端口映射描述")
    enabled: bool = Field(True, description="是否启用")
    lease_duration: int = Field(0, description="租期(秒)，0表示永久") 