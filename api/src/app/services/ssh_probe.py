"""An external TCP observer reached over SSH; no local reachability fallback."""

import asyncio
import datetime
import hashlib
import ipaddress
import json
import os
import re
import secrets
import shlex
import shutil
import stat
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..schemas.relay import validate_host
from .logger import logger
from .process_guard import guarded_command


_REMOTE_COMMAND = "/usr/bin/python3 -c " + shlex.quote(Path(__file__).with_name("remote_tcp_probe.py").read_text())


def _target(host, port):
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


class SSHProbeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    host: str
    user: str
    port: int = Field(default=22, ge=1, le=65535)
    identity_file: str
    known_hosts_file: str
    binary: str = "/usr/bin/ssh"
    allowed_targets: list[str] = Field(min_length=1, max_length=16)
    expected_hostname_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("host")
    @classmethod
    def valid_host(cls, value):
        if not value:
            raise ValueError("Probe SSH host is required")
        return validate_host(value)

    @field_validator("user")
    @classmethod
    def valid_user(cls, value):
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", value):
            raise ValueError("Invalid probe SSH user")
        return value

    @field_validator("identity_file", "known_hosts_file")
    @classmethod
    def file_reference(cls, value):
        if not value or any(c in value for c in ("\x00", "\n", "\r")):
            raise ValueError("Invalid probe file reference")
        return str(Path(value).expanduser().resolve())

    @field_validator("binary")
    @classmethod
    def executable(cls, value):
        if not value or any(c in value for c in ("\x00", "\n", "\r")):
            raise ValueError("Invalid probe executable")
        return value

    @field_validator("allowed_targets")
    @classmethod
    def targets(cls, values):
        for target in values:
            host, separator, raw_port = target.rpartition(":")
            host = host[1:-1] if host.startswith("[") and host.endswith("]") else host
            if not separator or not host or not raw_port.isdecimal():
                raise ValueError("Invalid probe target")
            validate_host(host)
            if not 1 <= int(raw_port) <= 65535 or target != _target(host, int(raw_port)):
                raise ValueError("Invalid probe target")
        return values


def load_ssh_probe(path: str):
    try:
        reference = Path(path).expanduser().absolute()
        if not path or reference.is_symlink():
            raise ValueError
        info = reference.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError
        config = SSHProbeConfig.model_validate(json.loads(reference.read_text()))
        return SSHProbe(config)
    except (OSError, ValueError, RuntimeError):
        raise ValueError("Unable to load private SSH probe configuration; check its format, ownership and permissions") from None


class SSHProbe:
    _TIMEOUT = 10.0
    _BODY_LIMIT = 4096
    _STOP_TIMEOUT = 3.0

    def __init__(self, config: SSHProbeConfig):
        self.config = config

    def _command(self, binary):
        hosts = '"' + self.config.known_hosts_file.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return guarded_command((
            binary, "-F", "/dev/null", "-T", "-p", str(self.config.port),
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
            "-o", f"UserKnownHostsFile={hosts}", "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes", "-o", "ControlMaster=no", "-o", "ControlPath=none",
            "-o", "ConnectTimeout=5", "-o", "ServerAliveInterval=3", "-o", "ServerAliveCountMax=1",
            "-i", self.config.identity_file, f"{self.config.user}@{self.config.host}", _REMOTE_COMMAND,
        ))

    async def external(self, host: str, port: int) -> bool:
        target, nonce = _target(host, port), secrets.token_hex(32)
        result, process, evidence, reason = False, None, {}, "not_allowed"
        try:
            if target not in self.config.allowed_targets:
                return False
            binary = shutil.which(self.config.binary)
            if not binary:
                reason = "ssh_unavailable"
                return False
            payload = json.dumps({"host": host, "port": port, "nonce": nonce,
                                  "allowed_targets": self.config.allowed_targets}).encode() + b"\n"
            reason = "probe_interrupted"
            async with asyncio.timeout(self._TIMEOUT):
                spawn = asyncio.create_task(asyncio.create_subprocess_exec(
                    *self._command(str(Path(binary).resolve())), stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                ))
                try:
                    process = await asyncio.shield(spawn)
                except asyncio.CancelledError:
                    process = await spawn
                    raise
                process.stdin.write(payload)
                await process.stdin.drain()
                process.stdin.close()
                try:
                    body = await process.stdout.readexactly(self._BODY_LIMIT + 1)
                except asyncio.IncompleteReadError as error:
                    body = error.partial
                if len(body) > self._BODY_LIMIT:
                    reason = "oversized_response"
                    return False
                if await process.wait() != 0:
                    reason = "ssh_failed"
                    return False
                evidence = self._verify(json.loads(body), nonce, target, port)
                result = evidence["success"]
                reason = "success" if result else "remote_failed"
                return result
        except asyncio.CancelledError:
            reason = "cancelled"
            raise
        except (OSError, ValueError, TypeError, KeyError, TimeoutError):
            reason = "invalid_or_unavailable_response"
            return False
        finally:
            if process is not None:
                await self._stop(process)
            # Only validated fields are logged, never untrusted stdout/stderr,
            # key contents, SSH credentials, configuration paths or API tokens.
            logger.info("External SSH probe " + json.dumps({
                "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "target": target, "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
                "success": result, "reason": reason, "ssh_exit": process.returncode if process else None,
                **evidence,
            }, separators=(",", ":")))

    def _verify(self, data, nonce, target, port):
        if (not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1
                or data.get("nonce") != nonce or data.get("target") != target
                or data.get("hostname_sha256") != self.config.expected_hostname_sha256
                or type(data.get("success")) is not bool):
            raise ValueError("Probe response mismatch")
        checked = datetime.datetime.fromisoformat(data["checked_at"])
        if checked.tzinfo is None:
            raise ValueError("Probe timestamp is missing its timezone")
        addresses = data["resolved_ips"]
        if not isinstance(addresses, list) or len(addresses) > 32:
            raise ValueError("Invalid probe DNS result")
        for value in addresses:
            address = ipaddress.ip_address(value)
            if not address.is_global or address.is_multicast:
                raise ValueError("Non-global probe DNS result")
        if data["success"]:
            peer = str(ipaddress.ip_address(data["peer_ip"]))
            if peer not in addresses or type(data["peer_port"]) is not int or data["peer_port"] != port:
                raise ValueError("Probe peer mismatch")
        return {"success": data["success"], "remote_checked_at": checked.isoformat(),
                "hostname_sha256": data["hostname_sha256"], "resolved_ips": addresses,
                "peer_ip": data["peer_ip"] if data["success"] else None,
                "peer_port": data["peer_port"] if data["success"] else None}

    async def _stop(self, process):
        if process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        try:
            await asyncio.wait_for(process.wait(), self._STOP_TIMEOUT)
        except (TimeoutError, asyncio.CancelledError) as error:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await asyncio.wait_for(process.wait(), self._STOP_TIMEOUT)
            if isinstance(error, asyncio.CancelledError):
                raise
