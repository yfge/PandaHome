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

Feature `f4ff4f501c6cff3a72bab2fed767901fd1d88316` committed with normal hooks.
API-only deployment and automatic TCP/UI three-state verification passed. Two
natural healthy cycles preceded a real probe-trust failure (SSH255/false), then
exact-byte restoration and two fresh healthy cycles. Native six/API identities
remained stable across negative/recovery; home HTTP200/version1.22.2 confirmed
business continuity independently. Prior manual takeover evidence is unchanged.

## Verification

- Backend freeze-v2: 10 current paths match; seven product/config paths retain v1 bytes.
- Backend owner: 141 focused tests passed; eight official-native/P2P/TLS cases passed without skip; Ruff/diff check passed.
- Independent UE: 70 SSH/HTTPS/guard tests passed; v2 fixture separately reviewed.
- Integration: `python -m pytest api/tests/test_ssh_probe.py -q -k 'guard_preserves_short_native_exit_code or killed_watchdog_cannot_leave_live_native or backend_sigkill_stops_short_probe_owner_chain or timeout_and_cancellation_reap_owned_guard_and_native'`: v1 actual 1 (1 failed/5 passed), preserved; v2 actual 0 (6 passed/23 deselected, 4.41s). Cold fixture cancellation now has independent readiness/deadline; real timeout and cleanup assertions remain.
- `PANDAHOME_FRP_BIN_DIR=<this-run>/native-bin pre-commit run --all-files --verbose`: actual 0, 457 backend passed/0 skips (57.49s), 121 web passed, Ruff/ESLint/all hooks passed. No SKIP. Unchanged web build/type are not repeated.
- Feature commit: actual 0, normal mandatory hooks without bypass.
- `deployment_control.py prepare/deploy --execute`: actual 0; reviewed six-source/API-only switch with 180s rollback protection. Original API63226/native identities stopped; API78361 owns the new native six. Web60342 unchanged.
- `observe_cycles.py --phase initial --expect true --cycles 2 --timeout 110 --execute`: actual 0, last_checked06:25:11.783990Z/06:25:26.514114Z, real home nonce/pin/global DNS/actual TCPpeer/SSHexit0.
- `deny-probe` then natural `negative --expect false --cycles 1`: actual 0; 06:26:40.555940Z/SSHexit255/probe_failed. 90s independent trust-restore watchdog protected the probe-only rename. `home_business_control.py --phase negative --execute`: HTTP200/version1.22.2/actual peer47.94.235.35; native/API identities unchanged.
- `restore-trust` at06:27:20 UTC restored original SHA5a0c2c2b19f0adba16ed7375f4ef9e2fe8925f9d90d29ef64c7c7e5a7cdc01dc; natural `recovery --expect true --cycles 2`: actual 0, last_checked06:27:27.239201Z/06:27:41.417689Z. New distinct fresh nonces; all three phase proofs bind exact same source/config/profile/API/native identities and zero manual detect/check paths.
- Independent real browser automatically displayed verified → needs attention/probe failed → verified from original GET/state responses, without writes or manual wake. Final independent UI/code PASS: 16 original UI automatic GET200 plus one CORS OPTIONS, three accepted/viewed screenshots, manual/mutation0; Chrome78383/all children/observer78400 gone, CDP19451 closed and owned auth profile deleted. Report SHA1197de3251d850615de1de1202001a35a8f4bfc48ffb461543443f46f847f650; manifest4ccd736caa91199f2c9eb3d6fb458544e02ad689136721a15deade549b4284fc; handoff72428e192c4002d0f28f58b89be4e8a40266b5e40674bff47da3ca5138cd4b97. All files/bytes/SHA in independent manifest were re-read.
- `final_audit.py --execute`: actual 0, 15/15 checks true, 290 deployed source hashes, provider full original DNS/ID/timestamps, cloud frps531881/config unchanged, private0600 files and loopback management. API log byte offsets, reviewed same-value DNS path and equal provider fields jointly support zero DNS writes. Snapshot UTC06:28:13; later ordinary GET is recorded separately.
- Temporary probe SSH/guards were absent in an observed quiet gap; persistent probe config/trust intentionally retained, original key only referenced. No home install/listener/files, routes/VPN/SG/firewall/router/DNS write.
- Private evidence root: `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/29/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/automatic-probe-20261029-055543Z`.

## Next steps

Final ordinary authenticated GET at06:31:53.487552 UTC read last_checked06:31:46.163239Z, healthy/verifiedtrue and the same API/native identities. Both independent watchdog immutable identities were gone after accepted release; browser owner released all temporary resources.

Integration: final five documentation paths use normal hooks, then freeze all
private evidence and hand clean HEAD to PM for independent review. No implementation
or staging is handed to PM; later ACKs must not append shared files.
Automatic TCP proof does not claim HTTP semantics or business-outage simulation.
Source/env backups, original cold-test failure and prior frozen evidence remain.
Company-WAN inbound, native P2P and historical mapping drift remain open. No push.
