from functools import lru_cache
from typing import List, Sequence

from fastapi import Depends, Request
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
    hashing_schemes: Sequence[str]
    if isinstance(settings.AUTH_HASHING_SCHEMES, (list, tuple)):
        hashing_schemes = settings.AUTH_HASHING_SCHEMES
    else:
        hashing_schemes = [
            scheme.strip()
            for scheme in str(settings.AUTH_HASHING_SCHEMES).split(",")
            if scheme.strip()
        ]
        if not hashing_schemes:
            hashing_schemes = ["bcrypt"]

    return AuthSettings(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_url=settings.AUTH_TOKEN_URL,
        hashing_schemes=list(hashing_schemes),
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


async def oauth2_scheme(
    request: Request,
    auth_settings: AuthSettings = Depends(get_auth_settings),
) -> str:
    scheme = _build_oauth2_scheme(auth_settings.token_url)
    return await scheme(request)
