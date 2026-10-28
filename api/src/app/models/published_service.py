"""Persisted desired public entries; transient evidence lives in runtime JSON."""

from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, Integer, String, UniqueConstraint

from ..database.database import Base


class PublishedService(Base):
    __tablename__ = "published_services"
    __table_args__ = (UniqueConstraint("public_port", "protocol", name="uq_published_port_protocol"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    local_ip = Column(String(15), nullable=False)
    local_port = Column(Integer, nullable=False)
    public_port = Column(Integer, nullable=False)
    protocol = Column(String(3), nullable=False, default="TCP")
    mode = Column(String(6), nullable=False, default="auto")
    domain = Column(String(253), nullable=False, default="")
    rr = Column(String(253), nullable=False, default="@")
    enabled = Column(Boolean, nullable=False, default=True)
    lease_duration = Column(Integer, nullable=False, default=3600)
    owner_token = Column(String(32), nullable=False, default=lambda: uuid4().hex)
    runtime = Column(JSON, nullable=False, default=dict)
