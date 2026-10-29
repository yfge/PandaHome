"""SSH ownership tests use local fixtures, never an external SSH server."""

import asyncio
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from src.app.services.relay_ssh import RelaySSHConfig, RelaySSHError, SSHControlTunnel


def config(tmp_path, **changes):
    for name in ("identity", "hosts"):
        (tmp_path / name).touch(mode=0o600)
    return RelaySSHConfig(host="ssh.example.com", user="root", identity_file=str(tmp_path / "identity"),
                          known_hosts_file=str(tmp_path / "hosts"), **changes)


def test_ssh_command_has_pinned_hosts_no_shell_or_credentials(tmp_path):
    tunnel = SSHControlTunnel(config(tmp_path), "127.0.0.1", 58354)
    tunnel.local_port = 58356
    args = tunnel._command("/usr/bin/ssh")
    assert args[0] == sys.executable and Path(args[1]).name == "process_guard.py"
    assert "BatchMode=yes" in args and "StrictHostKeyChecking=yes" in args
    assert "ExitOnForwardFailure=yes" in args and "UpdateHostKeys=no" in args
    assert "ControlMaster=no" in args and "ControlPath=none" in args
    assert "-F" in args and "/dev/null" in args
    assert "127.0.0.1:58356:127.0.0.1:58354" in args
    assert f'UserKnownHostsFile="{tmp_path / "hosts"}"' in args
    assert args[-1] == "root@ssh.example.com"


def test_openssh_parses_known_hosts_file_with_spaces_and_quotes(tmp_path):
    hosts = tmp_path / 'host directory' / 'known "hosts"'
    tunnel = SSHControlTunnel(RelaySSHConfig(host="ssh.example.com", user="root",
        identity_file=str(tmp_path / "identity"), known_hosts_file=str(hosts)), "127.0.0.1", 58354)
    tunnel.local_port = 58356
    guarded = tunnel._command("/usr/bin/ssh")
    command = ["/usr/bin/ssh", "-G", *guarded[8:]]
    result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0
    assert f"userknownhostsfile {hosts}" in result.stdout


@pytest.mark.parametrize("change", [
    {"user": "-oProxyCommand=evil"}, {"host": "ssh.example.com; touch bad"}, {"host": "-evil"},
    {"local_port": -1}, {"local_port": 65536}, {"identity_file": "inline\nkey"},
])
def test_ssh_option_injection_is_rejected(tmp_path, change):
    values = {"host": "ssh.example.com", "user": "root", "identity_file": str(tmp_path / "identity"),
              "known_hosts_file": str(tmp_path / "hosts"), **change}
    with pytest.raises(ValueError):
        RelaySSHConfig(**values)


def fake_ssh(tmp_path):
    binary = tmp_path / "ssh-fixture"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import socket, sys\n"
        "forward = sys.argv[sys.argv.index('-L')+1]\n"
        "port = int(forward.split(':')[1])\n"
        "with socket.socket() as listener:\n"
        "    listener.bind(('127.0.0.1', port))\n    listener.listen()\n"
        "    while True:\n        conn, _ = listener.accept()\n        conn.close()\n"
    )
    binary.chmod(0o700)
    return str(binary)


@pytest.mark.asyncio
async def test_owned_guard_restarts_crashed_carrier_and_releases_loopback_port(tmp_path):
    tunnel = SSHControlTunnel(config(tmp_path, binary=fake_ssh(tmp_path)), "127.0.0.1", 58354)
    old_port = None
    try:
        assert await tunnel.start() is True
        first = tunnel._process
        old_port = tunnel.local_port
        assert await tunnel.start() is False and tunnel._process is first
        first.kill()
        await asyncio.wait_for(first.wait(), 3)
        assert tunnel.status()["reason_code"] == "relay_ssh_process_exited"
        assert await tunnel.start() is True and tunnel._process is not first
        assert tunnel.status()["running"] is True
    finally:
        port = tunnel.local_port
        await tunnel.stop()
    for candidate in {port, old_port} - {None}:
        with socket.socket() as listener:
            assert listener.connect_ex(("127.0.0.1", candidate)) != 0
    assert tunnel.status()["running"] is False


@pytest.mark.asyncio
async def test_foreign_listener_is_never_adopted_or_stopped(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        tunnel = SSHControlTunnel(config(tmp_path, binary=fake_ssh(tmp_path), local_port=port), "127.0.0.1", 58354)
        with pytest.raises(RelaySSHError, match="Unable to establish"):
            await tunnel.start()
        assert tunnel._process is None and tunnel.status()["reason_code"] == "relay_ssh_start_failed"
        assert listener.getsockname()[1] == port


@pytest.mark.asyncio
async def test_failed_ssh_readiness_has_sanitized_error_and_reaps_guard(tmp_path):
    binary = tmp_path / "fail-ssh"
    binary.write_text(f"#!{sys.executable}\nimport sys\nprint('secret identity', file=sys.stderr)\nsys.exit(1)\n")
    binary.chmod(0o700)
    tunnel = SSHControlTunnel(config(tmp_path, binary=str(binary)), "127.0.0.1", 58354)
    tunnel._START_TIMEOUT = .3
    with pytest.raises(RelaySSHError) as error:
        await tunnel.start()
    assert "secret identity" not in str(error.value)
    assert tunnel._process is None
