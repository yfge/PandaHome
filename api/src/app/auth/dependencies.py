from functools import lru_cache
from typing import List

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from ..config import settings


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    token_url: str
    hashing_schemes: List[str]
    hashing_deprecated: str


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_url=settings.AUTH_TOKEN_URL,
        hashing_schemes=list(settings.AUTH_HASHING_SCHEMES),
        hashing_deprecated=settings.AUTH_HASHING_DEPRECATED,
    )


@lru_cache
def _build_password_context(schemes: tuple[str, ...], deprecated: str) -> CryptContext:
    return CryptContext(schemes=list(schemes), deprecated=deprecated)


def password_context() -> CryptContext:
    auth_settings = get_auth_settings()
    return _build_password_context(tuple(auth_settings.hashing_schemes), auth_settings.hashing_deprecated)


@lru_cache
def _build_oauth2_scheme(token_url: str) -> OAuth2PasswordBearer:
    return OAuth2PasswordBearer(tokenUrl=token_url)


def oauth2_scheme() -> OAuth2PasswordBearer:
    auth_settings = get_auth_settings()
    return _build_oauth2_scheme(auth_settings.token_url)
