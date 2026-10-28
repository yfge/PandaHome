"""Real-process lifecycle checks using only Python and loopback TCP payloads."""

import asyncio
import json
import os
import signal
import sys
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path

import psutil
import pytest

from src.app.services import process_guard
from src.app.services.relay import FrpRelay, RelayConfig, RelayMapping

GUARD = Path(process_guard.__file__).resolve()

PAYLOAD = """import json
import os
import signal
import socket
import sys
import time
from pathlib import Path
import psutil

if sys.argv[2] == 'ignore-term':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    time.sleep(float(sys.argv[3]))
    Path(sys.argv[1]).write_text(json.dumps({
        'pid': os.getpid(), 'created_at': psutil.Process().create_time(),
        'port': listener.getsockname()[1],
    }))
    while True:
        connection, _ = listener.accept()
        with connection:
            data = connection.recv(65536)
            connection.sendall(data)
"""

OWNER = """import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import psutil

config = json.loads(Path(sys.argv[1]).read_text())
if config['ignore_sigchld']:
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
guard = subprocess.Popen([
    sys.executable, config['guard'], '--parent', str(os.getpid()),
    '--parent-created-at', str(psutil.Process().create_time() + config['timestamp_shift']),
    '--', sys.executable, config['payload'], config['payload_ready'], config['term_mode'], config['ready_delay'],
])
Path(config['guard_ready']).write_text(json.dumps({
    'pid': guard.pid, 'created_at': psutil.Process(guard.pid).create_time(),
}))
try:
    while guard.poll() is None:
        time.sleep(0.02)
finally:
    if guard.poll() is None:
        guard.terminate()
        try:
            guard.wait(timeout=3)
        except subprocess.TimeoutExpired:
            guard.kill()
            guard.wait(timeout=3)
raise SystemExit(guard.returncode or 0)
"""


@dataclass(frozen=True)
class Identity:
    pid: int
    created_at: float

    @classmethod
    def of(cls, process):
        return cls(process.pid, process.create_time())

    def process(self):
        try:
            current = psutil.Process(self.pid)
            if current.create_time() == self.created_at and current.status() != psutil.STATUS_ZOMBIE:
                return current
        except psutil.Error:
            pass
        return None

    def signal(self, signum):
        current = self.process()
        if current is not None:
            with suppress(psutil.NoSuchProcess):
                current.send_signal(signum)


async def _wait_json(path, *, owner=None):
    deadline = asyncio.get_running_loop().time() + 8
    while asyncio.get_running_loop().time() < deadline:
        try:
            return json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            if owner is not None:
                assert owner.returncode is None, "Guard owner exited before child readiness"
            await asyncio.sleep(0.02)
    pytest.fail("Guarded Python payload did not become ready")


async def _wait_dead(*identities):
    deadline = asyncio.get_running_loop().time() + 6
    while asyncio.get_running_loop().time() < deadline:
        if all(identity.process() is None for identity in identities):
            return
        await asyncio.sleep(0.02)
    pytest.fail("Guarded processes survived their bounded cleanup interval")


async def _echo(port):
    reader, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), timeout=1)
    try:
        writer.write(b"guard-liveness-proof")
        await writer.drain()
        assert await asyncio.wait_for(reader.readexactly(20), timeout=1) == b"guard-liveness-proof"
    finally:
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()


def _descendants(owner):
    with suppress(psutil.NoSuchProcess):
        return [Identity.of(process) for process in psutil.Process(owner.pid).children(recursive=True)]
    return []


@asynccontextmanager
async def _running_guard(
    tmp_path, *, ignore_term=False, timestamp_shift=0, ready_delay=0, await_payload=True, ignore_sigchld=False,
):
    payload_script, owner_script = tmp_path / "payload.py", tmp_path / "owner.py"
    payload_script.write_text(PAYLOAD)
    owner_script.write_text(OWNER)
    payload_ready, guard_ready = tmp_path / "payload.json", tmp_path / "guard.json"
    arguments = tmp_path / "arguments.json"
    arguments.write_text(json.dumps({
        "guard": str(GUARD), "payload": str(payload_script), "payload_ready": str(payload_ready),
        "guard_ready": str(guard_ready), "term_mode": "ignore-term" if ignore_term else "default-term",
        "ready_delay": str(ready_delay), "timestamp_shift": timestamp_shift, "ignore_sigchld": ignore_sigchld,
    }))
    owner = await asyncio.create_subprocess_exec(
        sys.executable, str(owner_script), str(arguments),
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    owner_identity = Identity.of(psutil.Process(owner.pid))
    identities = []
    try:
        guard_data = await _wait_json(guard_ready, owner=owner)
        guard_identity = Identity(**guard_data)
        identities.append(guard_identity)
        payload_data = None
        if await_payload:
            payload_data = await _wait_json(payload_ready, owner=owner)
            identities.append(Identity(payload_data["pid"], payload_data["created_at"]))
        identities.extend(_descendants(owner))
        yield owner, owner_identity, guard_identity, payload_data, payload_ready, identities
    finally:
        identities.extend(_descendants(owner))
        if payload_ready.is_file():
            with suppress(json.JSONDecodeError):
                data = json.loads(payload_ready.read_text())
                identities.append(Identity(data["pid"], data["created_at"]))
        owner_identity.signal(signal.SIGTERM)
        with suppress(TimeoutError):
            await asyncio.wait_for(owner.wait(), timeout=2)
        for identity in reversed(identities):
            identity.signal(signal.SIGKILL)
        owner_identity.signal(signal.SIGKILL)
        with suppress(TimeoutError):
            await asyncio.wait_for(owner.wait(), timeout=2)
        await _wait_dead(*identities)


def test_guarded_command_captures_backend_identity_and_preserves_native_arguments(tmp_path):
    native = ("/usr/local/bin/frpc", "-c", str(tmp_path / "private config.toml"))
    command = process_guard.guarded_command(native)
    expected = (
        sys.executable, str(GUARD), "--parent", str(os.getpid()),
        "--parent-created-at", repr(psutil.Process().create_time()), "--", *native,
    )
    assert command == expected
    assert float(command[5]) == psutil.Process().create_time()


def test_guarded_command_is_idempotent_for_shared_and_p2p_adapters(tmp_path):
    native = ("/usr/local/bin/frpc", "-c", str(tmp_path / "frpc.toml"))
    wrapped = process_guard.guarded_command(native)
    assert process_guard.guarded_command(wrapped) == wrapped
    assert wrapped.count(str(GUARD)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("target,signum,ignore_sigchld", [
    ("guard", signal.SIGTERM, False), ("backend", signal.SIGKILL, False),
    ("guard", signal.SIGKILL, False), ("watchdog", signal.SIGKILL, False),
    ("watchdog", signal.SIGKILL, True),
])
async def test_guard_closes_payload_when_guard_or_backend_stops(tmp_path, target, signum, ignore_sigchld):
    async with _running_guard(tmp_path, ignore_sigchld=ignore_sigchld) as stack:
        owner, owner_identity, guard_identity, data, _, identities = stack
        await _echo(data["port"])
        target_identity = owner_identity if target == "backend" else guard_identity
        if target == "watchdog":
            watchdogs = guard_identity.process().children()
            assert len(watchdogs) == 1, "Outer guard did not own one cleanup watchdog"
            target_identity = Identity.of(watchdogs[0])
        target_identity.signal(signum)
        await _wait_dead(*identities)
        await asyncio.wait_for(owner.wait(), timeout=3)
        with pytest.raises((OSError, TimeoutError, asyncio.IncompleteReadError)):
            await _echo(data["port"])


@pytest.mark.asyncio
@pytest.mark.skipif(os.name != "posix", reason="Process-group isolation is a POSIX boundary")
async def test_watchdog_group_cleanup_preserves_another_guarded_service(tmp_path):
    first_directory, second_directory = tmp_path / "first", tmp_path / "second"
    first_directory.mkdir()
    second_directory.mkdir()
    async with _running_guard(first_directory) as first, _running_guard(second_directory) as second:
        first_owner, _, first_guard, first_data, _, first_identities = first
        _, _, second_guard, second_data, _, _ = second
        await _echo(first_data["port"])
        await _echo(second_data["port"])
        first_watchdogs = first_guard.process().children()
        second_watchdogs = second_guard.process().children()
        assert len(first_watchdogs) == len(second_watchdogs) == 1
        first_watchdog, second_watchdog = first_watchdogs[0], second_watchdogs[0]
        first_group, second_group = os.getpgid(first_watchdog.pid), os.getpgid(second_watchdog.pid)
        assert os.getsid(first_watchdog.pid) == first_group == first_watchdog.pid
        assert os.getsid(second_watchdog.pid) == second_group == second_watchdog.pid
        assert os.getpgid(first_data["pid"]) == first_group
        assert os.getpgid(second_data["pid"]) == second_group
        assert first_group != second_group
        Identity.of(first_watchdog).signal(signal.SIGKILL)
        await _wait_dead(*first_identities)
        await asyncio.wait_for(first_owner.wait(), timeout=3)
        with pytest.raises((OSError, TimeoutError, asyncio.IncompleteReadError)):
            await _echo(first_data["port"])
        # A successful independent roundtrip proves group cleanup stayed within
        # its owned service instead of signaling other native sessions.
        await _echo(second_data["port"])
        assert second_guard.process() is not None


@pytest.mark.asyncio
async def test_parent_timestamp_mismatch_refuses_to_launch_payload(tmp_path):
    async with _running_guard(tmp_path, timestamp_shift=-60, await_payload=False) as stack:
        owner, _, guard_identity, _, payload_ready, _ = stack
        result = await asyncio.wait_for(owner.wait(), timeout=3)
        await _wait_dead(guard_identity)
        assert result == 1, "Parent identity mismatch did not use the guard refusal path"
        assert not payload_ready.exists(), "Guard launched payload with an unrelated parent identity"


@pytest.mark.asyncio
async def test_native_ignoring_sigterm_is_killed_within_bound(tmp_path):
    async with _running_guard(tmp_path, ignore_term=True) as stack:
        owner, _, guard_identity, data, _, identities = stack
        await _echo(data["port"])
        guard_identity.signal(signal.SIGTERM)
        await _wait_dead(*identities)
        await asyncio.wait_for(owner.wait(), timeout=3)


@pytest.mark.asyncio
async def test_guard_killed_before_payload_announces_readiness_cannot_orphan_it(tmp_path):
    async with _running_guard(tmp_path, ready_delay=1, await_payload=False) as stack:
        owner, _, guard_identity, _, payload_ready, identities = stack
        deadline = asyncio.get_running_loop().time() + 4
        while asyncio.get_running_loop().time() < deadline:
            children = psutil.Process(owner.pid).children(recursive=True)
            natives = [process for process in children if str(tmp_path / "payload.py") in process.cmdline()]
            if natives:
                identities.extend(Identity.of(process) for process in children)
                break
            await asyncio.sleep(0.01)
        else:
            pytest.fail("Payload was not launched during startup-race regression")
        guard_identity.signal(signal.SIGKILL)
        await _wait_dead(*identities)
        await asyncio.wait_for(owner.wait(), timeout=3)
        assert not payload_ready.exists(), "Payload survived guard death long enough to announce readiness"


@pytest.mark.asyncio
async def test_relay_force_kill_does_not_orphan_sigterm_ignoring_payload(tmp_path):
    payload_script, ready = tmp_path / "payload.py", tmp_path / "relay-payload.json"
    payload_script.write_text(PAYLOAD)

    class GuardedRelay(FrpRelay):
        def _render_config(self, mappings):
            return "# Python lifecycle test; no external relay connection\n"

        def _process_command(self, binary):
            return (
                sys.executable, str(GUARD), "--parent", str(os.getpid()),
                "--parent-created-at", str(psutil.Process().create_time()), "--",
                sys.executable, str(payload_script), str(ready), "ignore-term", "0",
            )

    relay = GuardedRelay(RelayConfig(state_dir=tmp_path / "state", server_addr="unused", binary=sys.executable))
    identities = []
    try:
        await relay.apply([RelayMapping(1, "127.0.0.1", 80, 18080, "TCP")])
        data = await _wait_json(ready, owner=relay._process)
        guard = relay._process
        guard_identity = Identity.of(psutil.Process(guard.pid))
        identities = [guard_identity, Identity(data["pid"], data["created_at"])]
        identities.extend(Identity.of(process) for process in psutil.Process(guard.pid).children(recursive=True))
        await _echo(data["port"])
        # Freeze only the outer guard so FrpRelay must exercise its force-kill path.
        guard_identity.signal(signal.SIGSTOP)
        relay._STOP_TIMEOUT = 0.05
        await relay.stop()
        assert guard.returncode == -signal.SIGKILL, "Relay did not exercise forced guard termination"
        await _wait_dead(*identities)
        assert not relay._config_path.exists()
        with pytest.raises((OSError, TimeoutError, asyncio.IncompleteReadError)):
            await _echo(data["port"])
    finally:
        with suppress(Exception):
            await relay.stop()
        for identity in reversed(identities):
            identity.signal(signal.SIGKILL)
        await _wait_dead(*identities)
