from pathlib import Path
from typing import List, Optional

from pydantic import Field, SecretStr
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
    AUTH_TOKEN_URL: str = Field(default="/api/auth/token")

    ACCESS_CHECK_INTERVAL_SECONDS: int = Field(default=60, ge=15, le=3600)
    ACCESS_PROBE_URL: str = ""
    ACCESS_ALERT_WEBHOOK: str = ""
    ACCESS_ALERT_FAILURE_THRESHOLD: int = Field(default=3, ge=1, le=100)
    RELAY_BINARY: str = "frpc"
    RELAY_SERVER_ADDR: str = ""
    RELAY_SERVER_PORT: int = Field(default=7000, ge=1, le=65535)
    RELAY_PUBLIC_HOST: str = ""
    RELAY_TOKEN: SecretStr = SecretStr("")
    RELAY_STATE_DIR: Path = Field(default_factory=lambda: Path.home() / ".local/state/pandahome")



settings = Settings()
