from pydantic import BaseModel

class SetupRequest(BaseModel):
    """一站式设置服务请求"""
    domain: str
    rr: str
    external_port: int
    internal_port: int
    protocol: str = "TCP" 