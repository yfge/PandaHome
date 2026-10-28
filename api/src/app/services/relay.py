"""Manage the native frp client; its process state is not tunnel health proof."""

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .relay_status import FrpStatusClient


class RelayError(RuntimeError):
    """A sanitized relay lifecycle failure, safe to show in application logs."""


@dataclass(frozen=True, kw_only=True)
class RelayConfig:
    state_dir: Path
    binary: str = "frpc"
    server_addr: str = ""
    server_port: int = 7000
    public_host: str = ""
    token: str = field(default="", repr=False)


@dataclass(frozen=True)
class RelayMapping:
    service_id: int
    local_ip: str
    local_port: int
    public_port: int
    protocol: str


def _toml_string(value: str) -> str:
    # TOML basic strings share JSON escapes. Escape DEL and frp's Go-template
    # opener as well, so tokens containing {{ ... }} remain literal values.
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f").replace("{{", "\\u007b{")


def _validate_mappings(mappings: Sequence[RelayMapping]) -> None:
    names, ports = set(), set()
    for mapping in mappings:
        if mapping.protocol not in {"TCP", "UDP"}:
            raise ValueError("Relay protocol must be TCP or UDP")
        if not isinstance(mapping.service_id, int) or mapping.service_id < 1:
            raise ValueError("Relay service ID must be a positive integer")
        if not mapping.local_ip.strip():
            raise ValueError("Relay local address is required")
        for port in (mapping.local_port, mapping.public_port):
            if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
                raise ValueError("Relay ports must be integers between 1 and 65535")
        name, port = (mapping.service_id, mapping.protocol), (mapping.public_port, mapping.protocol)
        if name in names or port in ports:
            raise ValueError("Relay mappings must have unique service names and public ports per protocol")
        names.add(name)
        ports.add(port)


def _render(config: RelayConfig, mappings: Sequence[RelayMapping]) -> str:
    if (
        isinstance(config.server_port, bool)
        or not isinstance(config.server_port, int)
        or not 1 <= config.server_port <= 65535
    ):
        raise ValueError("Relay server port must be an integer between 1 and 65535")
    _validate_mappings(mappings)
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
    for mapping in sorted(mappings, key=lambda item: (item.service_id, item.protocol)):
        lines.extend(
            [
                "",
                "[[proxies]]",
                f'name = "pandahome-{mapping.service_id}-{mapping.protocol.lower()}"',
                f'type = "{mapping.protocol.lower()}"',
                f"localIP = {_toml_string(mapping.local_ip)}",
                f"localPort = {mapping.local_port}",
                f"remotePort = {mapping.public_port}",
            ]
        )
    return "\n".join(lines) + "\n"


class FrpRelay:
    """One owner per state directory, normally the application's lifespan.

    frpc owns tunnel transport, authentication and reconnects. Use an external
    probe to verify public reachability; a live child can still be reconnecting.
    """

    _STOP_TIMEOUT = 3.0

    def __init__(self, config: RelayConfig):
        self.config = config
        self._directory = Path(config.state_dir).expanduser().resolve() / "frp"
        self._config_path = self._directory / "frpc.toml"
        self._process: asyncio.subprocess.Process | None = None
        self._rendered: str | None = None
        self._reason_code: str | None = None
        self._lock = asyncio.Lock()
        self._status_client = FrpStatusClient()
        self._registration_names: dict[str, int] = {}
        self._registration_current = False
        for parent in Path(__file__).resolve().parents:
            if (parent / ".git").exists() and self._directory.is_relative_to(parent):
                raise RelayError("Relay state directory must be outside the source checkout")

    def _binary(self) -> str | None:
        binary = shutil.which(self.config.binary)
        return str(Path(binary).resolve()) if binary else None

    def status(self) -> dict:
        """Return local lifecycle facts only; never claim the relay is online."""
        configured = bool(self.config.server_addr.strip())
        available = self._binary() is not None
        running = self._process is not None and self._process.returncode is None
        if not configured:
            reason = "relay_not_configured"
        elif running:
            reason = None
        elif not available:
            reason = "relay_binary_missing"
        elif self._process is not None:
            reason = "relay_process_exited"
        else:
            reason = self._reason_code or "relay_stopped"
        return {
            "configured": configured,
            "available": available,
            "running": running,
            "public_host": (self.config.public_host.strip() or self.config.server_addr.strip()) or None,
            "reason_code": reason,
        }

    async def apply(self, mappings: Sequence[RelayMapping]) -> None:
        """Reconcile desired mappings, restarting only for changes or an exit."""
        async with self._lock:
            self._registration_current = False
            binary = self._binary()
            if not mappings or not self.config.server_addr.strip() or not binary:
                await self._stop_locked()
                return
            rendered = self._render_config(mappings)
            if self._process is not None and self._process.returncode is None and rendered == self._rendered:
                self._registration_current = True
                return
            await self._stop_locked()
            self._write_config(rendered)
            try:
                await self._start(binary)
            except BaseException:
                self._remove_config()
                raise
            self._rendered = rendered
            self._reason_code = None
            self._registration_current = True

    def _render_config(self, mappings: Sequence[RelayMapping]) -> str:
        """Allow another private transport adapter to share process ownership."""
        rendered = _render(self.config, mappings)
        self._registration_names = {
            f"pandahome-{mapping.service_id}-{mapping.protocol.lower()}": mapping.service_id for mapping in mappings
        }
        return self._status_client.configuration() + rendered

    async def registration(self) -> dict[int, bool]:
        """Return native acceptance for owned proxies, separate from reachability."""
        async with self._lock:
            if not self._registration_current or self._process is None or self._process.returncode is not None:
                return {}
            result = await self._status_client.registration(self._registration_names)
            return result if self._process.returncode is None else dict.fromkeys(result, False)

    def _process_command(self, binary: str) -> tuple[str, ...]:
        """Allow a transport adapter to supervise its child without shell parsing."""
        return binary, "-c", str(self._config_path)

    async def _start(self, binary: str) -> None:
        # Shield creation so cancellation cannot lose the handle to a new child.
        spawn = asyncio.create_task(
            asyncio.create_subprocess_exec(
                *self._process_command(binary),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=str(self._directory),
            )
        )
        try:
            self._process = await asyncio.shield(spawn)
        except asyncio.CancelledError:
            try:
                self._process = await spawn
            except OSError:
                pass
            else:
                await self._terminate()
            raise
        except OSError:
            self._reason_code = "relay_start_failed"
            raise RelayError("Unable to start the relay client") from None

    async def stop(self) -> None:
        """Terminate the owned child and remove only this adapter's config."""
        async with self._lock:
            await self._stop_locked()

    async def _stop_locked(self) -> None:
        try:
            await self._terminate()
        finally:
            self._registration_current = False
            self._remove_config()
            self._rendered = None
            self._reason_code = "relay_stopped"

    async def _terminate(self) -> None:
        process = self._process
        if process is None:
            return
        try:
            if process.returncode is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
            await asyncio.wait_for(process.wait(), timeout=self._STOP_TIMEOUT)
        except (TimeoutError, asyncio.CancelledError) as error:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(process.wait(), timeout=self._STOP_TIMEOUT)
            except TimeoutError:
                raise RelayError("Unable to stop the relay client") from None
            self._process = None
            if isinstance(error, asyncio.CancelledError):
                raise
        else:
            self._process = None

    def _write_config(self, rendered: str) -> None:
        try:
            if self._directory.is_symlink():
                raise OSError("Relay directory cannot be a symlink")
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self._directory.stat().st_uid != os.getuid():
                raise OSError("Relay directory must belong to this user")
            self._directory.chmod(0o700)
            fd, temporary = tempfile.mkstemp(prefix=".frpc-", suffix=".tmp", dir=self._directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(rendered)
                os.replace(temporary, self._config_path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        except OSError:
            self._reason_code = "relay_config_failed"
            raise RelayError("Unable to write private relay configuration") from None

    def _remove_config(self) -> None:
        self._config_path.unlink(missing_ok=True)
