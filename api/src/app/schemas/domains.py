from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class DomainSummary(BaseModel):
    domain: str
    id: str
    status: str


class DomainRecord(BaseModel):
    # Keep Aliyun's field casing to remain compatible with the existing frontend.
    Status: str
    RR: str
    Line: str
    Locked: bool
    Type: str
    DomainName: str
    Value: str
    RecordId: str
    TTL: int
    CreateTimestamp: int
    UpdateTimestamp: Optional[int] = None
    Priority: Optional[int] = None
    Weight: Optional[int] = None


class DomainRecordCreateRequest(BaseModel):
    rr: str = Field(..., min_length=1, description="Host record (RR), e.g. www")
    type: Literal["A", "AAAA", "CNAME", "TXT"] = Field("A", description="DNS record type")
    value: str = Field(..., min_length=1, description="DNS record value")
    ttl: Optional[int] = Field(default=None, ge=1, le=86400, description="TTL in seconds")
    line: Optional[str] = Field(default=None, description="DNS line, e.g. default")
    priority: Optional[int] = Field(default=None, ge=1, le=10, description="MX priority (if applicable)")


class DomainRecordUpdateRequest(BaseModel):
    rr: Optional[str] = Field(default=None, min_length=1)
    type: Optional[Literal["A", "AAAA", "CNAME", "TXT"]] = None
    value: Optional[str] = Field(default=None, min_length=1)
    ttl: Optional[int] = Field(default=None, ge=1, le=86400)
    line: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=10)

    @model_validator(mode="after")
    def _require_updates(self) -> "DomainRecordUpdateRequest":
        if all(
            value is None
            for value in (
                self.rr,
                self.type,
                self.value,
                self.ttl,
                self.line,
                self.priority,
            )
        ):
            raise ValueError("At least one field must be provided to update a record.")
        return self


class DomainRecordWriteResponse(BaseModel):
    record_id: str
    request_id: Optional[str] = None
