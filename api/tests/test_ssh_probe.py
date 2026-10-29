"""External probe protocol and owned subprocess tests never contact a real host."""

import asyncio
import datetime
import os
import subprocess
import socket
import sys
from contextlib import suppress
from pathlib import Path
from unittest.mock import Mock

import psutil
import pytest

from src.app.services import remote_tcp_probe as worker
from src.app.services.access.health import HealthChecks
from src.app.services.ssh_probe import SSHProbe, SSHProbeConfig, load_ssh_probe


TARGET = "gpufree-code.lets-gpt.com:8081"
HOST_SHA = "a" * 64


def config(tmp_path, **changes):
    return SSHProbeConfig(host="192.168.1.81", user="operator", identity_file=str(tmp_path / "key"),
        known_hosts_file=str(tmp_path / 'known "hosts" file'), allowed_targets=[TARGET],
        expected_hostname_sha256=HOST_SHA, **changes)


def fake_ssh(tmp_path, mode):
    binary = tmp_path / f"ssh-{mode}"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import sys, json, time, os\nfrom pathlib import Path\n"
        "p=json.loads(sys.stdin.buffer.readline())\n"
        f"mode={mode!r}\n"
        f"Path({str(tmp_path / 'ready')!r}).write_text(str(os.getpid()))\n"
        "if mode in ('timeout','cancel'): time.sleep(30)\n"
        "if mode=='nonzero': sys.exit(255)\n"
        "if mode=='malformed': print('not-json'); sys.exit(0)\n"
        "if mode=='oversized': print('x'*5000); sys.exit(0)\n"
        "result={'version':1,'nonce':p['nonce'],'target':p['host']+':'+str(p['port']),"
        f"'hostname_sha256':{HOST_SHA!r},"
        "'checked_at':'2026-10-29T06:00:00+00:00','success':mode!='refused',"
        "'resolved_ips':['47.94.235.35'],'peer_ip':'47.94.235.35','peer_port':p['port']}\n"
        "if mode=='wrongnonce': result['nonce']='0'*64\n"
        "if mode=='wrongtarget': result['target']='other.example.com:8081'\n"
        "if mode=='wronghost': result['hostname_sha256']='b'*64\n"
        "if mode=='wrongpeer': result['peer_ip']='8.8.8.8'\n"
        "if mode=='privateDNS': result['resolved_ips']=['192.168.1.81']\n"
        "if mode=='truthy': result['success']='true'\n"
        "print(json.dumps(result),flush=True)\n"
        "if mode=='nonzero_success': sys.exit(7)\n"
    )
    binary.chmod(0o700)
    return str(binary)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,expected", [
    ("success", True), ("refused", False), ("nonzero", False), ("malformed", False),
    ("wrongnonce", False), ("wrongtarget", False), ("wronghost", False), ("wrongpeer", False),
    ("privateDNS", False), ("truthy", False), ("oversized", False),
    ("nonzero_success", False),
])
async def test_owned_subprocess_response_is_strictly_bound(tmp_path, mode, expected):
    probe = SSHProbe(config(tmp_path, binary=fake_ssh(tmp_path, mode)))
    assert await probe.external("gpufree-code.lets-gpt.com", 8081) is expected
    pid = int((tmp_path / "ready").read_text())
    assert not psutil.pid_exists(pid)


@pytest.mark.asyncio
async def test_disallowed_target_never_spawns_ssh(tmp_path):
    probe = SSHProbe(config(tmp_path, binary=fake_ssh(tmp_path, "success")))
    assert await probe.external("gpufree-code.lets-gpt.com", 8082) is False
    assert not (tmp_path / "ready").exists()


def alive(process):
    try:
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.Error:
        return False


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [True, False])
async def test_timeout_and_cancellation_reap_owned_guard_and_native(tmp_path, cancel):
    probe = SSHProbe(config(tmp_path, binary=fake_ssh(tmp_path, "cancel")))
    # Cancellation starts after native readiness, separately from the genuine
    # one-second timeout case. Cold interpreter/guard startup can exceed 1s.
    probe._TIMEOUT = 10 if cancel else 1
    task = asyncio.create_task(probe.external("gpufree-code.lets-gpt.com", 8081))
    try:
        startup_deadline = asyncio.get_running_loop().time() + 5
        while not (tmp_path / "ready").exists():
            assert not task.done()
            assert asyncio.get_running_loop().time() < startup_deadline
            await asyncio.sleep(.01)
        native = psutil.Process(int((tmp_path / "ready").read_text()))
        watchdog, guard = native.parent(), native.parent().parent()
        if cancel:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            assert await task is False
        assert not any(alive(process) for process in (native, watchdog, guard))
    finally:
        if not task.done():
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_killed_watchdog_cannot_leave_live_native_or_claim_success(tmp_path):
    probe = SSHProbe(config(tmp_path, binary=fake_ssh(tmp_path, "cancel")))
    task = asyncio.create_task(probe.external("gpufree-code.lets-gpt.com", 8081))
    while not (tmp_path / "ready").exists():
        assert not task.done()
        await asyncio.sleep(.01)
    native = psutil.Process(int((tmp_path / "ready").read_text()))
    watchdog, guard = native.parent(), native.parent().parent()
    watchdog.kill()
    # The monitor is gone while its owned native is still executing: the outer
    # guard must kill the reserved group, not treat monitor death as completion.
    assert alive(native)
    assert await task is False
    assert not any(alive(process) for process in (native, watchdog, guard))


@pytest.mark.asyncio
@pytest.mark.parametrize("code", [0, 7])
async def test_guard_preserves_short_native_exit_code(code):
    from src.app.services.process_guard import guarded_command
    process = await asyncio.create_subprocess_exec(
        *guarded_command((sys.executable, "-c", f"raise SystemExit({code})")),
        stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    assert await asyncio.wait_for(process.wait(), 5) == code


@pytest.mark.asyncio
async def test_backend_sigkill_stops_short_probe_owner_chain(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(config(tmp_path, binary=fake_ssh(tmp_path, "cancel")).model_dump_json())
    script = tmp_path / "owner.py"
    script.write_text(
        "import asyncio, sys\nfrom src.app.services.ssh_probe import load_ssh_probe\n"
        "asyncio.run(load_ssh_probe(sys.argv[1]).external('gpufree-code.lets-gpt.com',8081))\n"
    )
    settings_path.chmod(0o600)
    owner = await asyncio.create_subprocess_exec(sys.executable, str(script), str(settings_path),
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    members = []
    try:
        deadline = asyncio.get_running_loop().time() + 5
        while not (tmp_path / "ready").exists():
            assert owner.returncode is None and asyncio.get_running_loop().time() < deadline
            await asyncio.sleep(.01)
        native = psutil.Process(int((tmp_path / "ready").read_text()))
        members = [native, native.parent(), native.parent().parent()]
        assert members[-1].ppid() == owner.pid
        owner.kill()
        await asyncio.wait_for(owner.wait(), 3)
        while any(alive(p) for p in members) and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(.01)
        assert not any(alive(p) for p in members)
    finally:
        if owner.returncode is None:
            owner.kill()
            await owner.wait()
        for member in members:
            if alive(member):
                member.kill()


@pytest.mark.parametrize("live_group", [True, False])
def test_guard_permission_error_requires_both_dead_leader_and_empty_group(monkeypatch, live_group):
    from src.app.services import process_guard as guard
    watcher = Mock(pid=1234, wait=Mock(return_value=0))
    identity = Mock(create_time=Mock(return_value=1))
    monkeypatch.setattr(guard.psutil, "Process", lambda *_: identity)
    monkeypatch.setattr(guard, "_alive", lambda *_: False)
    monkeypatch.setattr(guard, "_group_has_live_members", lambda *_: live_group)
    monkeypatch.setattr(guard.os, "killpg", Mock(side_effect=PermissionError))
    if live_group:
        with pytest.raises(PermissionError):
            guard._stop_watchdog(watcher)
        watcher.wait.assert_not_called()
    else:
        assert guard._stop_watchdog(watcher) == 0


def test_unreadable_process_group_is_never_considered_empty(monkeypatch):
    from src.app.services import process_guard as guard
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1234])
    monkeypatch.setattr(guard.os, "getpgid", Mock(side_effect=PermissionError))
    assert guard._group_has_live_members(1234) is True


def test_command_pins_known_hosts_and_keeps_target_and_nonce_off_shell(tmp_path):
    probe = SSHProbe(config(tmp_path))
    command = probe._command("/usr/bin/ssh")
    assert "StrictHostKeyChecking=yes" in command and "BatchMode=yes" in command
    assert "IdentitiesOnly=yes" in command and "ControlMaster=no" in command and "ControlPath=none" in command
    assert 'UserKnownHostsFile="' in " ".join(command)
    assert TARGET not in command[-1] and "a" * 64 not in command[-1]
    assert command[-1].startswith("/usr/bin/python3 -c ")
    ssh_argv = ["/usr/bin/ssh", "-G", *command[8:]]
    parsed = subprocess.run(ssh_argv, capture_output=True, text=True, timeout=5)
    assert parsed.returncode == 0
    assert f'userknownhostsfile {probe.config.known_hosts_file}' in parsed.stdout


def test_private_config_load_failure_is_explicit_and_never_uses_another_provider(tmp_path):
    path = tmp_path / "probe.json"
    path.write_text(config(tmp_path).model_dump_json())
    path.chmod(0o600)
    assert load_ssh_probe(str(path)).config.host == "192.168.1.81"
    path.chmod(0o644)
    with pytest.raises(ValueError, match="ownership and permissions"):
        load_ssh_probe(str(path))
    path.chmod(0o600)
    path.write_text('{"secret":"do-not-echo",broken')
    with pytest.raises(ValueError) as error:
        load_ssh_probe(str(path))
    assert "do-not-echo" not in str(error.value)
    with pytest.raises(ValueError):
        HealthChecks(probe_provider="ssh", probe_ssh_config_file=str(tmp_path / "missing"))


def test_fifo_config_is_rejected_without_reading_or_blocking(tmp_path):
    path = tmp_path / "fifo"
    os.mkfifo(path, mode=0o600)
    with pytest.raises(ValueError, match="Unable to load"):
        load_ssh_probe(str(path))


@pytest.mark.asyncio
async def test_explicit_ssh_failure_does_not_fall_back_to_https(tmp_path, monkeypatch):
    path = tmp_path / "probe.json"
    path.write_text(config(tmp_path, binary=fake_ssh(tmp_path, "nonzero")).model_dump_json())
    path.chmod(0o600)
    checks = HealthChecks(probe_provider="ssh", probe_ssh_config_file=str(path),
                          probe_url="https://probe.example.com/probe")
    import src.app.services.access.health as module
    monkeypatch.setattr(module.aiohttp, "ClientSession", Mock(side_effect=AssertionError("No HTTPS fallback")))
    assert await checks.external("gpufree-code.lets-gpt.com", 8081, "TCP") is False
    assert await checks.external("gpufree-code.lets-gpt.com", 8081, "UDP") is None


def payload():
    return {"host": "gpufree-code.lets-gpt.com", "port": 8081, "nonce": "1" * 64, "allowed_targets": [TARGET]}


@pytest.mark.parametrize("listening", [True, False])
def test_remote_program_dials_fresh_resolution_and_observes_real_tcp_result(monkeypatch, listening):
    original_socket = socket.socket
    listener = original_socket()
    listener.bind(("127.0.0.1", 0))
    local_port = listener.getsockname()[1]
    if listening:
        listener.listen()
    else:
        listener.close()
    resolved = []
    dialed = []

    def resolve(host, port, **kwargs):
        resolved.append((host, port))
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("47.94.235.35", port))]

    class FixtureSocket:
        def __init__(self, *args):
            self.socket = original_socket(*args)
        def __enter__(self):
            return self
        def __exit__(self, *_):
            self.socket.close()
        def settimeout(self, value):
            self.socket.settimeout(value)
        def connect(self, address):
            # Controlled DNS/socket metadata fixtures route only the TCP syscall
            # to a disposable local listener; this is not public field evidence.
            dialed.append(address)
            self.socket.connect(("127.0.0.1", local_port))
        def getpeername(self):
            return "47.94.235.35", 8081

    monkeypatch.setattr(worker.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(worker.socket, "socket", FixtureSocket)
    try:
        result = worker.probe(payload())
        assert result["success"] is listening
        assert resolved == [("gpufree-code.lets-gpt.com", 8081)]
        assert dialed == [("47.94.235.35", 8081)]
        assert result["nonce"] == "1" * 64 and result["target"] == TARGET
        assert datetime.datetime.fromisoformat(result["checked_at"]).tzinfo is not None
    finally:
        listener.close()


def test_remote_program_rejects_non_global_dns_before_connect(monkeypatch):
    monkeypatch.setattr(worker.socket, "getaddrinfo", lambda *a, **kw: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 8081))])
    connect = Mock(side_effect=AssertionError("No non-global connection"))
    monkeypatch.setattr(worker.socket, "socket", connect)
    assert worker.probe(payload())["success"] is False
    connect.assert_not_called()
