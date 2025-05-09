from typing import Any, Optional
from pydantic import BaseModel

class Response(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success"):
        """成功响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = 500):
        """错误响应"""
        return cls(code=code, message=message) 