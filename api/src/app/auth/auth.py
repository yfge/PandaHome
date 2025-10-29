from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.user import UserRole
from ..models.db_models import User
from .dependencies import AuthSettings, get_auth_settings, oauth2_scheme, password_context


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    context = password_context()
    return context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    context = password_context()
    return context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    auth_settings: Optional[AuthSettings] = None,
) -> str:
    """创建访问令牌"""
    auth_settings = auth_settings or get_auth_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_settings: AuthSettings = Depends(get_auth_settings),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[auth_settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def check_permission(user: User, required_role: UserRole) -> bool:
    """检查用户权限"""
    role_hierarchy = {
        UserRole.ADMIN: 3,
        UserRole.USER: 2,
        UserRole.GUEST: 1,
    }
    return role_hierarchy[user.role] >= role_hierarchy[required_role]
