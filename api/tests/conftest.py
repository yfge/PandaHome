import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.app.auth.auth import get_password_hash
from src.app.config import settings
from src.app.database.database import Base, get_db
from src.app.main import app

# Disable slow startup/shutdown handlers (UPnP discovery) during tests.
app.router.on_startup.clear()
app.router.on_shutdown.clear()
from src.app.models.db_models import User
from src.app.models.user import UserRole


@pytest.fixture()
def tmp_db_path() -> Generator[str, None, None]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = f"sqlite:///{path}"
    try:
        yield path
    finally:
        settings.DATABASE_URL = original_url
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture()
def db_session(tmp_db_path: str) -> Generator[Session, None, None]:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def normal_user(db_session: Session) -> User:
    user = User(
        username="user",
        email="user@example.com",
        hashed_password=get_password_hash("userpass"),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user
