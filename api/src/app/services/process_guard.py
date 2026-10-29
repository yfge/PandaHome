"""Supervise a native process across backend or individual monitor death.

Executed by absolute file path so the guard never initializes the application.
The command line carries executable/config paths only, never credentials.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Sequence

import psutil


_POLL_SECONDS = 0.05
_TERM_SECONDS = 1.0
_WATCHDOG_GRACE_SECONDS = 2.0


def guarded_command(command: Sequence[str]) -> tuple[str, ...]:
    """Capture immutable backend identity before either monitor is launched."""
    command = tuple(command)
    helper = str(Path(__file__).resolve())
    # Adapters may wrap an already guarded base command during integration.
    if len(command) >= 2 and command[:2] == (sys.executable, helper):
        return command
    parent = psutil.Process()
    return (
        sys.executable, helper, "--parent", str(parent.pid),
        "--parent-created-at", repr(parent.create_time()), "--", *command,
    )


def _alive(process: psutil.Process, created_at: float) -> bool:
    try:
        return (
            process.create_time() == created_at
            and process.is_running()
            and process.status() != psutil.STATUS_ZOMBIE
        )
    except psutil.Error:
        return False


class _Stop:
    def __init__(self):
        self.requested = False
        signal.signal(signal.SIGTERM, self._signal)
        signal.signal(signal.SIGINT, self._signal)

    def _signal(self, _signum, _frame):
        self.requested = True


def _stop_native(child: subprocess.Popen) -> int:
    if child.poll() is None:
        with suppress(ProcessLookupError):
            child.terminate()
        try:
            child.wait(timeout=_TERM_SECONDS)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                child.kill()
            child.wait(timeout=_TERM_SECONDS)
    return child.returncode or 0


def _group_has_live_members(group_id: int) -> bool:
    """Fail closed if the reserved group still contains work or cannot be read."""
    for pid in psutil.pids():
        try:
            if os.getpgid(pid) == group_id and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE:
                return True
        except (ProcessLookupError, psutil.NoSuchProcess):
            continue
        except (OSError, psutil.Error):
            return True
    return False


def _watchdog(args, command: tuple[str, ...], parent: psutil.Process) -> int:
    """Own native creation so outer-guard death cannot leave a launch gap."""
    stop = _Stop()
    guard = psutil.Process(args.guard)
    if not _alive(parent, args.parent_created_at) or not _alive(guard, args.guard_created_at):
        return 1
    if stop.requested:
        return 1
    child = subprocess.Popen(command)
    try:
        while (
            child.poll() is None and not stop.requested
            and _alive(parent, args.parent_created_at) and _alive(guard, args.guard_created_at)
        ):
            time.sleep(_POLL_SECONDS)
    finally:
        _stop_native(child)
    return child.returncode or 0


def _stop_watchdog(watcher: subprocess.Popen) -> int:
    """Clean its owned POSIX group before reaping the leader, avoiding PID reuse."""
    identity = psutil.Process(watcher.pid)
    created_at = identity.create_time()
    if _alive(identity, created_at):
        with suppress(ProcessLookupError):
            watcher.terminate()
    deadline = time.monotonic() + _WATCHDOG_GRACE_SECONDS
    # Popen.poll()/wait() would reap the leader too early. Keep its PID reserved
    # until native descendants have been killed, even when the watchdog crashed.
    while _alive(identity, created_at) and time.monotonic() < deadline:
        time.sleep(_POLL_SECONDS)
    if os.name == "posix":
        try:
            os.killpg(watcher.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Darwin may report EPERM for an unreaped zombie-only group. A dead
            # leader alone is insufficient: its native child could be orphaned.
            # Keep the PID reserved and tolerate only an inspectably quiescent
            # group, never an unreadable group or a surviving native process.
            if _alive(identity, created_at) or _group_has_live_members(watcher.pid):
                raise
    elif _alive(identity, created_at):
        watcher.kill()
    return watcher.wait(timeout=_TERM_SECONDS)


def _guard(args, command: tuple[str, ...], parent: psutil.Process) -> int:
    stop = _Stop()
    if not _alive(parent, args.parent_created_at):
        return 1
    identity = psutil.Process()
    watcher = subprocess.Popen([
        sys.executable, str(Path(__file__).resolve()), "--watchdog",
        "--parent", str(args.parent), "--parent-created-at", repr(args.parent_created_at),
        "--guard", str(identity.pid), "--guard-created-at", repr(identity.create_time()),
        "--", *command,
    ], start_new_session=os.name == "posix")
    try:
        watched = psutil.Process(watcher.pid)
        started = watched.create_time()
        while _alive(watched, started) and not stop.requested and _alive(parent, args.parent_created_at):
            time.sleep(_POLL_SECONDS)
    finally:
        _stop_watchdog(watcher)
    return watcher.returncode or 0


def main() -> int:
    if os.name == "posix":
        # An inherited SIGCHLD=SIG_IGN would auto-reap the group leader before
        # group cleanup, removing the PID reservation this protocol relies on.
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=int, required=True)
    parser.add_argument("--parent-created-at", type=float, required=True)
    parser.add_argument("--watchdog", action="store_true")
    parser.add_argument("--guard", type=int)
    parser.add_argument("--guard-created-at", type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = tuple(args.command[1:] if args.command[:1] == ["--"] else args.command)
    if not command or (args.watchdog and (args.guard is None or args.guard_created_at is None)):
        return 2
    try:
        parent = psutil.Process(args.parent)
        return _watchdog(args, command, parent) if args.watchdog else _guard(args, command, parent)
    except (OSError, psutil.Error, subprocess.TimeoutExpired):
        # Native output is owned by frpc; do not log executable/config arguments.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
