"""Terminate an owned native child if its backend parent disappears.

Executed by absolute file path so the guard never initializes the application.
The command line carries executable/config paths only, never credentials.
"""

import argparse
import os
import signal
import subprocess
import time

import psutil


def _parent_alive(parent: psutil.Process) -> bool:
    try:
        return (
            os.getppid() == parent.pid
            and parent.is_running()
            and parent.status() != psutil.STATUS_ZOMBIE
        )
    except psutil.Error:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        return 2
    try:
        parent = psutil.Process(args.parent)
        if not _parent_alive(parent):
            return 1
    except psutil.Error:
        return 1

    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        child = subprocess.Popen(command)
    except OSError:
        return 1
    try:
        while child.poll() is None and not stopping and _parent_alive(parent):
            time.sleep(0.1)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=1)
    return child.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
