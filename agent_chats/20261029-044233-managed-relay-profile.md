## Summary

Implement administrator-managed relay configuration and product-owned SSH control transport for PandaHome. The PM delegates implementation and performs review; this agent owns only backend files and this log. Existing persistent GPUFree Git DNS and standalone relay processes are untouched by implementation and isolated tests.

## Changes

- `api/src/app/schemas/relay.py`: validated global relay profile, explicit credential replacement/removal, safe view with `has_token` and no credential echo.
- `api/src/app/services/relay_profile.py`: environment-compatible defaults, private 0600 atomic JSON storage outside the checkout, explicit failure for malformed/inaccessible profiles, and construction of the original relay adapter.
- `api/src/app/config.py`, `api/.env.example`: TLS verification and optional SSH environment defaults; managed profile overrides defaults after an administrator saves it.
- `api/src/app/services/relay_ssh.py`: argv-only native SSH, pinned known-host verification and key-file reference, loopback-only forwarding, guarded process ownership, readiness checks and bounded cleanup. No shell, password fallback, host-key acceptance or copied private key.
- `api/src/app/services/relay.py`: preserve configured CA/server-name checks, own SSH alongside frpc, restart frpc when its SSH carrier changes, stop both on an empty desired set, and invalidate native registration when either child exits. SSH/TLS status contains only nonsecret facts and remains separate from external reachability.
- `api/src/app/services/access/controller.py`: load the persisted profile through the normal App/controller path; serialize configuration changes with service reconciliation, prepare and fsync storage before stopping old children, atomically commit and replace the original relay reference, and wake maintenance. Unchanged saves do not restart children. No database schema change or automatic migration.
- `api/src/app/routers/access.py`: active-administrator-only `GET/PUT /api/access/relay-config`. Local request validation prevents Pydantic errors from echoing a replacement token. Omitted/null token preserves the credential; empty token or `clear_token=true` clears it; removal and nonempty replacement together are rejected.
- `api/tests/test_relay.py`, `api/tests/test_relay_ssh.py`, `api/tests/test_relay_profile.py`, `api/tests/test_relay_native.py`: meaningful configuration, private storage, authentication, safe error, lifecycle, OpenSSH path parsing and actual native TLS enforcement checks.

## Outcome

Backend implementation is ready for independent code review and integration. No staging or commit was performed by this agent. Existing cloud frps remains a configurable infrastructure dependency; the application now owns its SSH control carrier and native frpc whenever enabled published services require them. Configuration alone does not start children. The backend does not convert manual HTTP evidence into `external_verified=true`.

## Verification

- Dependency environment reused: `/opt/homebrew/Caskroom/miniconda/base/bin/python` (3.13.5), with existing editable PandaHome/test dependencies. No new dependency installation was required.
- Official matching native directory: `/var/folders/rc/ffg_cryd6jsbjc2srvhbqnc40000gn/T/pandahome-frp-smoke-u00bqj7x/frp_0.71.1_darwin_arm64` (0.71.1). Independent SHA review was supplied by the PM/integration owner. Tests listen only on loopback and generate disposable local certificates, not production credentials.
- `PANDAHOME_FRP_BIN_DIR=... PYTHONPATH=api python -m pytest -q api/tests/test_relay.py api/tests/test_relay_ssh.py api/tests/test_relay_profile.py api/tests/test_relay_native.py api/tests/test_access_controller.py api/tests/test_access_api.py api/tests/test_access_dns.py api/tests/test_p2p_native.py`: 152 passed in 27.81s; exit 0. Correct CA/name carried an actual TCP nonce; wrong CA and wrong name both rejected registration and exposed no business listener.
- `PYTHONPATH=api python -m pytest -q api/tests/test_p2p_service.py api/tests/test_p2p_api.py api/tests/test_p2p_migrations.py api/tests/test_transport_isolation.py`: 53 passed in 11.26s; exit 0.
- Final focused rerun after invalid `~user` path sanitization and the mid-registration carrier-exit assertion: `PANDAHOME_FRP_BIN_DIR=... PYTHONPATH=api python -m pytest -q api/tests/test_relay.py api/tests/test_relay_ssh.py api/tests/test_relay_profile.py api/tests/test_relay_native.py`: 57 passed in 12.40s; exit 0.
- Targeted Ruff and `git diff --check`: passed after the final code changes.
- One attempted command named nonexistent `api/tests/test_p2p.py`: pytest exit 4/no tests ran; corrected to the actual existing P2P modules above.
- Full shared hooks/build: Not run by this agent; the sole integration/index owner runs normal hooks and complete gates after PM review. No hook bypass.
- Live cutover, home-client verification, DNS readback and App restart recovery: Not run by this implementation agent; integration owner must execute the reviewed frozen plan.

## Next steps

- PM reviews the exact frozen backend source and isolated test evidence. Integration owner alone stages/commits the reviewed files with normal hooks.
- Independent UI and real App/controller acceptance must verify profile persistence, service enable/disable and API restart while preserving the existing DNS record, cloud frps and rollback bytes.
- On a rare final rename failure after children stop, the old persisted configuration and original relay instance remain paired; maintenance is woken to restart that original configuration. No different environment fallback occurs.
- The actual cloud SSH authentication, home-to-cloud business entry and removal of both old standalone launchd owners remain field acceptance work, not proven by the local SSH fixture or unit tests.
