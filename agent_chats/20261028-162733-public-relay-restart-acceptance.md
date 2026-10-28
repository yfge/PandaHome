## Summary

Close the coordinator's public relay architecture finding: backend SIGKILL must
release the old client so a replacement can restore the same published entry.
The shared Access/P2P implementation is already committed as `2e440ad`; this
follow-up strengthens its restart evidence without adding another supervisor.

## Changes

- `api/tests/test_relay.py`: extend the real default-FrpRelay backend-death test
  to two backend generations using the same state directory, generated proxy
  name and public port. The Python payload reads the generated TOML, announces
  its PID/creation time, and echoes TCP data. Each generation must disappear
  before cleanup; old readiness is removed before launching its replacement.
- `docs/public-access.md`: explain the subprocess restart proof and distinguish
  the native frpc PID from its guard in the existing real-frp smoke.
- `tasks.md`: explicitly close the Feature 07 guard/restart acceptance item.

## Outcome

- Read-only review confirmed `FrpRelay._process_command` uses the canonical
  `process_guard.guarded_command`; `_P2PRelay` inherits this seam unchanged.
  Public and private transports reuse the same implementation without nesting.
- The restart test checks owned processes and listener closure before its
  emergency cleanup. The final cleanup removes leftovers after a failed
  assertion without suppressing that failure.
- Native smoke resolves the actual frpc executable among descendants before
  SIGKILL, then verifies registration and TCP/UDP after reconciliation.
- Independent agent review of the shared seam and the new test found no issues.

## Verification

- `PYTHONPATH=api pytest -q api/tests/test_relay.py api/tests/test_process_guard.py api/tests/test_p2p_service.py api/tests/test_relay_status.py`: **87 passed**.
- Isolated committed-source snapshot plus this change, `PYTHONPATH=api pytest -q api/tests`: **359 passed, 4 skipped**; optional native tests are enabled separately below.
- `PANDAHOME_FRP_BIN_DIR=/path/to/verified/frp PYTHONPATH=api pytest -q api/tests/test_p2p_native.py`: **4 passed**, including native backend-SIGKILL cleanup and replacement revocation.
- `PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /path/to/verified/frp`: **passed** with previously SHA256-verified official frp v0.71.1 outside the checkout. Real loopback TCP/UDP, native registration, unrelated-port rejection, unchanged mapping identity, server reconnect, actual native-client crash recovery and cleanup all returned success.
- `ruff check api/tests/test_relay.py` and `git diff --check`: passed.
- `PYTHONPATH=api pre-commit run --all-files`: **passed** on rerun. The initial
  all-files run passed Python/API/frontend gates but corrected an existing
  extra EOF blank line in coordinator-owned `web/src/app/login/login-client.tsx`.
  That correction matches the primary checkout's existing WIP and stays outside
  this commit. The regular commit gate also runs all applicable mandatory hooks;
  no hooks are bypassed. Validation uses an isolated checkout to preserve parallel work.

## Next steps

No implementation work remains for this finding. The coordinator retains overall
independent acceptance. These results prove POSIX/local process recovery, not
physical home-router/public-network availability or instantaneous takeover while
old monitors are still shutting down. Keep real cross-network validation open.
No push, deployment, real router writes or DNS changes were performed.
