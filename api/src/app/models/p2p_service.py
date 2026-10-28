"""Desired private TCP services; credentials never enter ordinary API views."""

import secrets
from uuid import uuid4

from sqlalchemy import Boolean, Column, Integer, String

from ..database.database import Base


class P2PService(Base):
    __tablename__ = "p2p_services"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    local_ip = Column(String(15), nullable=False)
    local_port = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    fallback_enabled = Column(Boolean, nullable=False, default=True)
    uid = Column(String(32), nullable=False, unique=True, default=lambda: uuid4().hex)
    secret_key = Column(String(128), nullable=False, default=lambda: secrets.token_urlsafe(32))

    def __repr__(self) -> str:
        return f"P2PService(id={self.id!r}, enabled={self.enabled!r})"
