from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.app.models.db_models import User
from src.app.models.user import UserRole


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return token


def test_token_issued_for_valid_credentials(client: TestClient, admin_user: User) -> None:
    token = _login(client, "admin", "adminpass")
    assert token


def test_token_denied_for_invalid_credentials(client: TestClient, admin_user: User) -> None:
    response = client.post(
        "/api/auth/token",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 400


def test_admin_can_create_user(client: TestClient, admin_user: User, db_session: Session) -> None:
    token = _login(client, "admin", "adminpass")
    response = client.post(
        "/api/users/",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass",
            "role": "user",
            "is_active": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text

    created = db_session.query(User).filter(User.username == "newuser").first()
    assert created is not None
    assert created.role == UserRole.USER


def test_non_admin_cannot_create_user(client: TestClient, normal_user: User) -> None:
    token = _login(client, "user", "userpass")
    response = client.post(
        "/api/users/",
        json={
            "username": "blocked",
            "email": "blocked@example.com",
            "password": "blockedpass",
            "role": "user",
            "is_active": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_can_list_users(client: TestClient, admin_user: User) -> None:
    token = _login(client, "admin", "adminpass")
    response = client.get("/api/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_non_admin_cannot_list_users(client: TestClient, normal_user: User) -> None:
    token = _login(client, "user", "userpass")
    response = client.get("/api/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
