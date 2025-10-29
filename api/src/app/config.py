from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Global application settings loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库配置
    DATABASE_URL: str = Field(default="sqlite:///./app.db")

    # JWT配置
    SECRET_KEY: str = Field(default="change-me")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # 阿里云DNS配置
    ALIYUN_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = Field(default=None)
    ALIYUN_REGION_ID: str = Field(default="cn-hangzhou")

    # Auth settings
    AUTH_HASHING_SCHEMES: List[str] = Field(default_factory=lambda: ["bcrypt"])
    AUTH_HASHING_DEPRECATED: str = Field(default="auto")
    AUTH_TOKEN_URL: str = Field(default="token")


settings = Settings()
