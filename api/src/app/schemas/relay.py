"""Administrator-owned relay configuration; credentials never appear in views."""

import ipaddress
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


def validate_host(value: str) -> str:
    if not value:
        return value
    try:
        ipaddress.ip_address(value)
    except ValueError:
        if len(value) > 253 or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in value.rstrip(".").split(".")
        ):
            raise ValueError("Enter an IP address or hostname") from None
    return value


class RelayProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    server_addr: str = ""
    server_port: int = Field(default=7000, ge=1, le=65535)
    public_host: str = ""
    binary: str = Field(default="frpc", min_length=1, max_length=4096)
    tls_trusted_ca_file: str = Field(default="", max_length=4096)
    tls_server_name: str = Field(default="", max_length=253)
    ssh_enabled: bool = False
    ssh_host: str = ""
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: str = Field(default="", max_length=64)
    ssh_identity_file: str = Field(default="", max_length=4096)
    ssh_known_hosts_file: str = Field(default="~/.ssh/known_hosts", max_length=4096)
    ssh_local_port: int = Field(default=0, ge=0, le=65535)
    ssh_binary: str = Field(default="ssh", min_length=1, max_length=4096)
    # SecretStr intentionally preserves leading/trailing spaces in credentials.
    token: SecretStr | None = None
    clear_token: bool = False

    @field_validator("token", mode="wrap")
    @classmethod
    def credential(cls, value, handler):
        return SecretStr(value) if isinstance(value, str) else handler(value)

    @field_validator("binary", "ssh_binary")
    @classmethod
    def executable(cls, value: str) -> str:
        if any(character in value for character in ("\x00", "\n", "\r")):
            raise ValueError("Enter an executable name or path")
        return value

    @field_validator("server_addr", "public_host", "ssh_host", "tls_server_name")
    @classmethod
    def host(cls, value: str) -> str:
        return validate_host(value)

    @field_validator("ssh_user")
    @classmethod
    def user(cls, value: str) -> str:
        if value and not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", value):
            raise ValueError("Invalid SSH user")
        return value

    @field_validator("tls_trusted_ca_file", "ssh_identity_file", "ssh_known_hosts_file")
    @classmethod
    def path(cls, value: str) -> str:
        if any(character in value for character in ("\x00", "\n", "\r")):
            raise ValueError("Enter a file path")
        try:
            return str(Path(value).expanduser().resolve()) if value else ""
        except (OSError, RuntimeError):
            raise ValueError("Enter a valid file path") from None

    @model_validator(mode="after")
    def complete(self):
        if self.clear_token and self.token is not None and self.token.get_secret_value():
            raise ValueError("Credential replacement and removal cannot be combined")
        if self.ssh_enabled and not all((
            self.server_addr, self.public_host, self.ssh_host, self.ssh_user,
            self.ssh_identity_file, self.ssh_known_hosts_file,
        )):
            raise ValueError("SSH requires its endpoint, file references and a public relay host")
        if self.ssh_enabled:
            try:
                address = ipaddress.ip_address(self.public_host)
            except ValueError:
                pass
            else:
                if not address.is_global or address.is_multicast:
                    raise ValueError("The public relay host must be a global unicast address or hostname")
        return self

    def view(self, *, source: str) -> dict:
        return {
            **self.model_dump(exclude={"token", "clear_token"}),
            "has_token": bool(self.token and self.token.get_secret_value()), "source": source,
        }
