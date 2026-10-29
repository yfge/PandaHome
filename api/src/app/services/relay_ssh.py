"""Own an optional SSH carrier for the relay control connection, never a shell."""

import asyncio
import shutil
import socket
import re
from dataclasses import dataclass
from pathlib import Path

from .process_guard import guarded_command
from ..schemas.relay import validate_host


class RelaySSHError(RuntimeError):
    """Sanitized lifecycle error; native SSH output is never returned or logged."""


@dataclass(frozen=True, kw_only=True)
class RelaySSHConfig:
    host: str
    user: str
    identity_file: str
    known_hosts_file: str
    port: int = 22
    local_port: int = 0
    binary: str = "ssh"

    def __post_init__(self):
        for host in (self.host,):
            if not host or validate_host(host) != host:
                raise ValueError("Invalid SSH host")
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", self.user):
            raise ValueError("Invalid SSH user")
        for name, minimum in (("port", 1), ("local_port", 0)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= 65535:
                raise ValueError("Invalid SSH port")
        for name in ("identity_file", "known_hosts_file"):
            value = getattr(self, name)
            if not value or any(character in value for character in ("\x00", "\n", "\r")):
                raise ValueError("Invalid SSH file reference")
            object.__setattr__(self, name, str(Path(value).expanduser().resolve()))


class SSHControlTunnel:
    _START_TIMEOUT = 12.0
    _STOP_TIMEOUT = 3.0

    def __init__(self, config: RelaySSHConfig, remote_host: str, remote_port: int):
        if not remote_host or validate_host(remote_host) != remote_host:
            raise ValueError("Invalid relay control host")
        if isinstance(remote_port, bool) or not isinstance(remote_port, int) or not 1 <= remote_port <= 65535:
            raise ValueError("Invalid relay control port")
        self.config, self.remote_host, self.remote_port = config, remote_host, remote_port
        self._process = None
        self.local_port = None
        self._reason = "relay_stopped"

    def status(self) -> dict:
        available = shutil.which(self.config.binary) is not None
        running = self._process is not None and self._process.returncode is None
        reason = None if running else (
            "relay_ssh_binary_missing" if not available else
            "relay_ssh_process_exited" if self._process is not None else self._reason
        )
        return {"configured": True, "available": available, "running": running, "reason_code": reason}

    def _command(self, binary: str) -> tuple[str, ...]:
        remote = f"[{self.remote_host}]" if ":" in self.remote_host else self.remote_host
        # -o values have OpenSSH config syntax even without a shell. Quote the
        # path there as well as passing the entire option as one argv element.
        hosts = '"' + self.config.known_hosts_file.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return guarded_command((
            binary, "-F", "/dev/null", "-N", "-T", "-p", str(self.config.port),
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
            "-o", f"UserKnownHostsFile={hosts}",
            "-o", "GlobalKnownHostsFile=/dev/null", "-o", "IdentitiesOnly=yes",
            "-o", "ControlMaster=no", "-o", "ControlPath=none", "-o", "ConnectTimeout=10",
            "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
            "-i", self.config.identity_file,
            "-L", f"127.0.0.1:{self.local_port}:{remote}:{self.remote_port}",
            f"{self.config.user}@{self.config.host}",
        ))

    def _choose_port(self) -> int:
        # Do not reuse another process's existing listener as readiness proof.
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", self.config.local_port))
            return reservation.getsockname()[1]

    async def start(self) -> bool:
        """Return whether this invocation replaced the carrier identity/port."""
        if self.status()["running"]:
            return False
        await self.stop()
        binary = shutil.which(self.config.binary)
        try:
            if not binary or not all(Path(path).is_file() for path in (
                self.config.identity_file, self.config.known_hosts_file,
            )):
                raise OSError
            self.local_port = self._choose_port()
            spawn = asyncio.create_task(asyncio.create_subprocess_exec(
                *self._command(str(Path(binary).resolve())), stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            ))
            try:
                self._process = await asyncio.shield(spawn)
            except asyncio.CancelledError:
                self._process = await spawn
                raise
            await self._wait_ready()
            self._reason = None
            return True
        except BaseException as error:
            await self.stop()
            self._reason = "relay_ssh_start_failed"
            if isinstance(error, asyncio.CancelledError):
                raise
            raise RelaySSHError("Unable to establish the relay SSH connection") from None

    async def _wait_ready(self) -> None:
        deadline = asyncio.get_running_loop().time() + self._START_TIMEOUT
        while asyncio.get_running_loop().time() < deadline:
            if self._process.returncode is not None:
                raise OSError
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", self.local_port), .3)
                writer.close()
                await writer.wait_closed()
                # Allow ExitOnForwardFailure to propagate through both guards.
                await asyncio.sleep(.15)
                if self._process.returncode is not None:
                    raise OSError
                return
            except (OSError, TimeoutError):
                await asyncio.sleep(.05)
        raise TimeoutError

    async def stop(self) -> None:
        process = self._process
        if process is not None:
            try:
                if process.returncode is None:
                    process.terminate()
                await asyncio.wait_for(process.wait(), self._STOP_TIMEOUT)
            except ProcessLookupError:
                pass
            except (TimeoutError, asyncio.CancelledError) as error:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await asyncio.wait_for(process.wait(), self._STOP_TIMEOUT)
                if isinstance(error, asyncio.CancelledError):
                    raise
            finally:
                if process.returncode is not None:
                    self._process = None
        self.local_port = None
        self._reason = "relay_stopped"
