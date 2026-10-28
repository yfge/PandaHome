from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NetworkTopology = Literal["public_ipv4", "upstream_nat", "cgnat", "unknown"]
ConnectionMode = Literal["direct", "relay", "unknown"]


class NetworkReport(BaseModel):
    topology: NetworkTopology
    recommended_mode: ConnectionMode = Field(description="A recommendation, not proof of inbound reachability")
    observed_public_ip: str | None
    gateway_external_ip: str | None
    upnp_available: bool
    checked_at: datetime
    reason_code: str
