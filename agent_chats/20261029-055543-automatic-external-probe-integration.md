# Automatic external SSH probe integration

## Summary

Integrate a first-class trusted external TCP observer into the retained PandaHome
managed deployment. PM coordinates/read-only reviews; backend implements and
integration alone stages/commits/deploys. Existing business/DNS/cloud frps are kept.

## Changes

Backend owner changes `api/.env.example`, `api/src/app/config.py`,
`api/src/app/services/access/controller.py`, `api/src/app/services/access/health.py`,
`api/src/app/services/process_guard.py`, `api/src/app/services/remote_tcp_probe.py`,
`api/src/app/services/ssh_probe.py` and `api/tests/test_ssh_probe.py`; its frozen logs
are `agent_chats/20261029-060504-external-ssh-probe.md` and
`agent_chats/20261029-061023-probe-cancel-fixture.md`.
Integration updates `README.md`, `README.zh.md`, `docs/public-access.md`, `tasks.md`
and this log with the provider configuration, evidence boundary and deployment.

The explicitly selected SSH provider uses an existing identity by path, a private
probe-only host-key copy, exact target allowlist, nonce JSON stdin and fixed remote
Python. Home observer identity/DNS/actual peer/UTC and real SSH exit must validate.
No home listener/install/file, network rule, native relay config or UI change.
Darwin guard EPERM is tolerated only after reserved leader death and an inspectable
process group without live members; native exit codes and orphan cleanup remain.

## Outcome

Product and v2 independent code reviews passed. Runtime deployment and automatic
TCP/UI verification are pending; local tests are not public-connectivity evidence.
Prior takeover/manual business acceptance remains historical and unchanged.

## Verification

- Backend freeze-v2: 10 current paths match; seven product/config paths retain v1 bytes.
- Backend owner: 141 focused tests passed; eight official-native/P2P/TLS cases passed without skip; Ruff/diff check passed.
- Independent UE: 70 SSH/HTTPS/guard tests passed; v2 fixture separately reviewed.
- Integration: `python -m pytest api/tests/test_ssh_probe.py -q -k 'guard_preserves_short_native_exit_code or killed_watchdog_cannot_leave_live_native or backend_sigkill_stops_short_probe_owner_chain or timeout_and_cancellation_reap_owned_guard_and_native'`: v1 actual 1 (1 failed/5 passed), preserved; v2 actual 0 (6 passed/23 deselected, 4.41s). Cold fixture cancellation now has independent readiness/deadline; real timeout and cleanup assertions remain.
- `PANDAHOME_FRP_BIN_DIR=<this-run>/native-bin pre-commit run --all-files --verbose`: actual 0, 457 backend passed/0 skips (57.49s), 121 web passed, Ruff/ESLint/all hooks passed. No SKIP. Unchanged web build/type are not repeated.
- Feature commit uses normal mandatory hooks; runtime/source deployment remains pending at this commit.
- Private evidence root: `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/29/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/automatic-probe-20261029-055543Z`.

## Next steps

Integration: commit exact reviewed paths with normal hooks, then approved API-only
owned rollback deployment. Independently observe two natural healthy cycles,
probe-only trust failure, restoration and UI. No manual check/detect. Preserve
source/env backups, all genuine failures and prior frozen evidence. Company-WAN
inbound, native P2P and historical mapping drift remain open. No push is requested.
