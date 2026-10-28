"""Own private frp providers without treating a process as proof of a peer path."""

import asyncio
import os
import re
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from ..models.p2p_service import P2PService
from ..schemas.p2p import P2PServiceConfig, P2PServiceView
from .logger import logger
from .relay import FrpRelay, RelayConfig, _toml_string


@dataclass(frozen=True, kw_only=True)
class P2PConfig:
    state_dir: Path
    server_addr: str = ""
    server_port: int = 7000
    token: str = field(default="", repr=False)
    binary: str = "frpc"
    stun_server: str = "stun.easyvoip.com:3478"
    fallback_timeout_ms: int = 1500
    retry_interval_seconds: float = 10
    tls_trusted_ca_file: str = ""
    tls_server_name: str = ""

    def __post_init__(self) -> None:
        if self.tls_trusted_ca_file.strip():
            # frpc runs in its private state directory, not the backend cwd.
            object.__setattr__(self, "tls_trusted_ca_file", str(
                Path(self.tls_trusted_ca_file.strip()).expanduser().resolve()
            ))
        _validate_port(self.server_port)
        if (
            isinstance(self.fallback_timeout_ms, bool)
            or not isinstance(self.fallback_timeout_ms, int)
            or not 1 <= self.fallback_timeout_ms <= 60000
        ):
            raise ValueError("P2P fallback timeout must be between 1 and 60000 milliseconds")
        if (
            isinstance(self.retry_interval_seconds, bool)
            or not isinstance(self.retry_interval_seconds, (int, float))
            or not 0 < self.retry_interval_seconds <= 300
        ):
            raise ValueError("P2P retry interval must be positive and at most 300 seconds")


@dataclass(frozen=True)
class _Provider:
    uid: str
    local_ip: str
    local_port: int
    fallback_enabled: bool
    secret_key: str = field(repr=False)

    @classmethod
    def from_row(cls, row: P2PService) -> "_Provider":
        # Validate persisted intent too; callers outside HTTP can write the database.
        config = P2PServiceConfig(
            name=row.name, local_ip=row.local_ip, local_port=row.local_port,
            enabled=row.enabled, fallback_enabled=row.fallback_enabled,
        )
        if not isinstance(row.uid, str) or not re.fullmatch(r"[0-9a-f]{32}", row.uid):
            raise ValueError("P2P service identifier is invalid")
        if not isinstance(row.secret_key, str) or not row.secret_key:
            raise ValueError("P2P service credentials are missing")
        return cls(row.uid, config.local_ip, config.local_port, config.fallback_enabled, row.secret_key)

    def name(self, kind: str) -> str:
        return f"pandahome-p2p-{self.uid}-{kind}"


def _validate_port(port: int) -> None:
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("P2P port must be an integer between 1 and 65535")


def _common_lines(config: P2PConfig, *, visitor: bool = False) -> list[str]:
    lines = [
        f"serverAddr = {_toml_string(config.server_addr.strip())}",
        f"serverPort = {config.server_port}",
        "loginFailExit = false",
        "transport.tls.enable = true",
        'auth.method = "token"',
        f"auth.token = {_toml_string(config.token)}",
        'log.to = "console"',
        'log.level = "warn"',
        "log.disablePrintColor = true",
    ]
    if config.stun_server.strip():
        lines.append(f"natHoleStunServer = {_toml_string(config.stun_server.strip())}")
    if config.tls_trusted_ca_file.strip():
        ca_file = "frps-ca.crt" if visitor else config.tls_trusted_ca_file.strip()
        lines.append(f"transport.tls.trustedCaFile = {_toml_string(ca_file)}")
    if config.tls_server_name.strip():
        lines.append(f"transport.tls.serverName = {_toml_string(config.tls_server_name.strip())}")
    return lines


def _render_providers(config: P2PConfig, providers: Sequence[_Provider]) -> str:
    lines = _common_lines(config)
    for provider in sorted(providers, key=lambda item: item.uid):
        kinds = ("xtcp", "stcp") if provider.fallback_enabled else ("xtcp",)
        for kind in kinds:
            lines.extend([
                "", "[[proxies]]",
                f"name = {_toml_string(provider.name(kind))}",
                f"type = {_toml_string(kind)}",
                f"localIP = {_toml_string(provider.local_ip)}",
                f"localPort = {provider.local_port}",
                f"secretKey = {_toml_string(provider.secret_key)}",
                "transport.useEncryption = true",
            ])
    return "\n".join(lines) + "\n"


class _P2PRelay(FrpRelay):
    def __init__(self, config: P2PConfig):
        self._p2p_config = config
        super().__init__(RelayConfig(
            state_dir=Path(config.state_dir) / "p2p", binary=config.binary,
            server_addr=config.server_addr, server_port=config.server_port, token=config.token,
        ))

    def _render_config(self, mappings: Sequence[_Provider]) -> str:
        return _render_providers(self._p2p_config, mappings)

    def _process_command(self, binary: str) -> tuple[str, ...]:
        return (
            sys.executable, str(Path(__file__).with_name("process_guard.py")),
            "--parent", str(os.getpid()), "--", *super()._process_command(binary),
        )


class P2PManager:
    """Periodically reload persisted intent and restart a failed provider child."""

    def __init__(self, config: P2PConfig, session_factory):
        self.config = config
        self.session_factory = session_factory
        self.relay = _P2PRelay(config)
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._last_reason: str | None = None

    def status(self) -> dict:
        try:
            state = self.relay.status()
        except Exception:
            state = {
                "configured": bool(self.config.server_addr.strip()),
                "available": False, "running": False, "reason_code": "p2p_reconcile_failed",
            }
        reason = state["reason_code"]
        if reason:
            reason = reason.replace("relay_", "p2p_", 1)
        return {
            "configured": state["configured"], "available": state["available"],
            "running": state["running"], "reason_code": self._last_reason or reason,
            "connection_type": "unknown", "ca_required": bool(self.config.tls_trusted_ca_file.strip()),
        }

    def service_view(self, row: P2PService) -> P2PServiceView:
        state = self.status()
        if not row.enabled:
            status, reason = "disabled", "p2p_disabled"
        elif not state["configured"]:
            status, reason = "needs_setup", "p2p_not_configured"
        elif not state["available"]:
            status, reason = "needs_setup", "p2p_binary_missing"
        elif state["running"] and state["reason_code"] is None:
            status, reason = "awaiting_connection", "p2p_awaiting_connection"
        else:
            status, reason = "error", state["reason_code"] or "p2p_stopped"
        return P2PServiceView(
            id=row.id, name=row.name, local_ip=row.local_ip, local_port=row.local_port,
            enabled=row.enabled, fallback_enabled=row.fallback_enabled, status=status, reason_code=reason,
        )

    async def reconcile(self) -> None:
        async with self._lock:
            try:
                with self.session_factory() as db:
                    rows = db.query(P2PService).filter(P2PService.enabled.is_(True)).order_by(P2PService.id).all()
                    providers = [_Provider.from_row(row) for row in rows]
                await self.relay.apply(providers)
            except Exception:
                reason = "p2p_reconcile_failed"
                with suppress(Exception):
                    if self.relay.status()["reason_code"] == "relay_start_failed":
                        reason = "p2p_start_failed"
                with suppress(Exception):
                    await self.relay.stop()
                self._last_reason = reason
                logger.warning("P2P provider reconciliation failed")
            else:
                self._last_reason = None

    async def startup(self) -> None:
        if self._task is None:
            await self.reconcile()
            self._task = asyncio.create_task(self._run(), name="p2p-provider-maintenance")

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self.config.retry_interval_seconds)
            await self.reconcile()

    async def shutdown(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        await self.relay.stop()

    def render_visitor(self, row: P2PService, bind_port: int = 18080) -> str:
        """Export credentials only to the explicitly protected download endpoint."""
        _validate_port(bind_port)
        if not row.enabled:
            raise ValueError("Enable the P2P service before exporting a visitor")
        if not self.config.server_addr.strip():
            raise ValueError("Configure a P2P server before exporting a visitor")
        provider = _Provider.from_row(row)
        lines = _common_lines(self.config, visitor=True)
        kinds = ("stcp", "xtcp") if row.fallback_enabled else ("xtcp",)
        for kind in kinds:
            lines.extend([
                "", "[[visitors]]",
                f"name = {_toml_string(provider.name(kind) + '-visitor')}",
                f"type = {_toml_string(kind)}",
                f"serverName = {_toml_string(provider.name(kind))}",
                f"secretKey = {_toml_string(provider.secret_key)}",
                'bindAddr = "127.0.0.1"',
                f"bindPort = {bind_port if kind == 'xtcp' else -1}",
                "transport.useEncryption = true",
            ])
            if kind == "xtcp":
                lines.append("keepTunnelOpen = true")
                if row.fallback_enabled:
                    lines.extend([
                        f"fallbackTo = {_toml_string(provider.name('stcp') + '-visitor')}",
                        f"fallbackTimeoutMs = {self.config.fallback_timeout_ms}",
                    ])
        return "\n".join(lines) + "\n"
