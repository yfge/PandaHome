## Summary

Add an explicitly selected SSH external TCP observer when no existing remote HTTPS blackbox exporter is available. The existing HTTPS provider remains the default. This implementation agent changes backend files only; the PM coordinates/reviews, and the integration owner alone stages, commits and deploys.

## Changes

- `api/src/app/config.py`, `api/.env.example`: `ACCESS_PROBE_PROVIDER=https|ssh` and `ACCESS_PROBE_SSH_CONFIG_FILE`. The latter references an owner-only regular JSON file; no credential or private key text enters the API or source tree.
- `api/src/app/services/access/controller.py`, `api/src/app/services/access/health.py`: pass the explicit provider into the original health-check interface. SSH configuration errors fail closed, SSH failures return false, and no SSH-to-HTTPS/local fallback exists. Existing HTTPS URL validation, metrics parsing, UDP semantics and alert behavior remain unchanged.
- `api/src/app/services/ssh_probe.py`: fixed argv, strict SSH host checking, referenced key and probe-owned known_hosts file, no ControlMaster, bounded JSON stdin/stdout, per-request random nonce, exact target allowlist, expected external hostname SHA, actual exit status and remote DNS/global TCP-peer checks. Only validated, nonsecret structured audit fields are logged. Every local process is guarded and reaped after completion, timeout or cancellation.
- `api/src/app/services/remote_tcp_probe.py`: fixed dependency-free Python program that performs fresh DNS and TCP operations on the external device, receives JSON via stdin, and emits a nonce/target/hostname-bound result. The program never listens, installs or changes network configuration; a six-second alarm bounds DNS and socket lifetime.
- `api/src/app/services/process_guard.py`: preserve native exit codes for naturally completed short commands on Darwin. EPERM during reserved-group cleanup is tolerated only after the leader is dead and the complete process group is inspectably free of live members. Unknown group visibility or any live orphan remains a failure. The PID is not reaped before cleanup.
- `api/tests/test_ssh_probe.py`: subprocess protocol, actual local TCP success/refusal under explicit resolver/socket metadata fixtures, private configuration/FIFO rejection, nonce/target/hostname/peer mismatches, malformed or oversized output, SSH nonzero despite success JSON, strict known-host path parsing, timeout/cancellation/backend death, killed-watchdog orphan cleanup and short native exit 0/7 regression tests.

## Outcome

Implementation is ready for independent frozen-source review. No stage, commit, live SSH probe, cloud operation or runtime switch was executed by this agent. The deployment owner will use an exact single-target allowlist for `gpufree-code.lets-gpt.com:8081` and a probe-specific known_hosts copy, keeping the native relay's existing trust file unchanged.

The SSH JSON fields are `host`, `user`, `port` (22), `identity_file`, `known_hosts_file`, `binary` (`/usr/bin/ssh`), `allowed_targets` and mandatory `expected_hostname_sha256`. Invalid/missing/nonregular/unreadable/nonprivate JSON is an explicit sanitized startup error. A missing trust file or refused SSH connection during a running check yields false and the original `degraded/probe_failed/external_verified=false` transition.

## Verification

- Existing dependency environment `/opt/homebrew/Caskroom/miniconda/base/bin/python` (3.13.5) reused; no dependency installation, database migration or UI change.
- `PYTHONPATH=api python -m pytest -q api/tests/test_ssh_probe.py api/tests/test_access_health.py api/tests/test_access_controller.py api/tests/test_relay.py api/tests/test_relay_ssh.py`: 141 passed in 14.29s, exit 0. Includes unchanged HTTPS behavior, original controller behavior and real guarded subprocess lifetimes.
- Targeted Ruff and `git diff --check`: passed after code changes.
- `PANDAHOME_FRP_BIN_DIR=<previously verified matching official 0.71.1 native-bin> PYTHONPATH=api python -m pytest -q api/tests/test_p2p_native.py api/tests/test_transport_isolation.py api/tests/test_relay_native.py`: 8 passed in 19.65s, exit 0; no skipped native cases. This verifies existing private transport, public relay TLS and transport isolation after the shared guard fix.
- An initial focused run found that the unchanged guard turned short native exit 0 into exit 1 on Darwin. That real failure was fixed at its ownership boundary; SSH nonzero is never ignored. Earlier Ruff-only unused imports were removed.
- Full shared hooks/build: Not run by this agent; the sole integration owner runs normal gates after independent review. No hook bypass.
- Actual home-network automatic success/failure/recovery: Not run by this implementation agent. Local tests do not establish external reachability.

## Incident

During isolated SSH-probe tests, the original `6c8b40b` process guard returned 1 for native exit 0 and 7. A private instrumented copy preserved the original failure: Darwin `killpg` returned EPERM while the unreaped watchdog was a zombie and its group had no live members. The private reproduction JSON plus native stdout and full traceback remain under the automatic-probe run's `backend-review/`; no old evidence was overwritten. The fix checks the entire group, including possible reparented natives, before tolerating this natural-exit case. Tests prove that killing the watchdog while its native is alive still triggers complete group cleanup and a failed result.

## Next steps

- PM, independent UI reviewer and integration owner review the exact source hashes. Only the integration owner stages/commits with normal hooks and deploys.
- Verify natural controller cycles, with fresh nonce/remote timestamp and increasing original `last_checked`: success, actual probe-control trust failure, then recovery. Do not call manual check to simulate automatic polling.
- The planned probe-owned known_hosts interruption proves conservative failure when the external observer is unavailable, while the published business path stays operational. It must not be described as an 8081 business outage.
- Preserve existing managed relay, DNS, cloud frps, routes and security groups. Do not start old standalone jobs. Remote interpreter `/usr/bin/python3` must exist on the explicitly trusted observer.
