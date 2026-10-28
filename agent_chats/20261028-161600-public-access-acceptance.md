## Summary

Feature 07 implementation and local acceptance are complete. Overall independent review and real-network deployment remain separate evidence layers.

## Changes

- `docs/public-access.md`: final setup, environment/API reference, route maintenance, verification boundaries and shared process ownership behavior.
- `tasks.md`: complete Feature 07 Step 6 without closing Feature 08 external-network acceptance.
- This record links the delivered configuration, runtime, UI and atomic validation evidence.

## Outcome

- `api/src/app/services/network_detection.py` and `api/src/app/schemas/network.py`: conservative public IPv4/upstream NAT/CGNAT/unknown detection.
- `api/src/app/services/access/{controller,reconcile,mappings,dns,health,store}.py`, `api/src/app/routers/access.py`, `api/src/app/models/published_service.py`, `api/src/app/schemas/access.py`: persistent active-admin service management, DDNS, owned renewal/cleanup, relay fallback, independent probes and transition webhooks.
- `api/src/app/services/relay.py`, `relay_status.py`, `process_guard.py`: native frp transport, per-proxy registration and shared guarded ownership; existing gateway/DNS helpers reused.
- `web/src/app/access/`, `web/src/components/access/`, `web/src/types/access.ts` and both locale files: guided responsive setup, validation/error states and keyboard focus restoration.
- Design/implementation/UI commits: `6622de1`, `f7e05ad`, `c7bac83`, `8dab24d`, `37d913f`; prerequisite/shared refinements: `4d46ec9`, `0ca8a86`, `fd184be`, `521eea8`, `2e440ad`.

## Verification

- Final isolated integrated snapshot `PYTHONPATH=api pytest -q api/tests`: **359 passed, 4 skipped** (optional native P2P cases require explicit binary configuration).
- `npm run test --prefix web`: **60 passed**, including 18 actual Radix keyboard interaction regressions for public-access dialogs.
- `npm run lint --prefix web`, TypeScript and `npm run build --prefix web`: passed. The production build includes coordinator-owned Next16 params/login fixes copied unstaged for combined acceptance; those files are intentionally excluded from this delivery.
- `pre-commit run --all-files`: passed; all implementation commits ran mandatory hooks without skips. Isolated snapshots avoid stashing active parallel work; verified commits were fast-forwarded with exact-path index updates. Final publications hold the primary index lock and preserve other staged work.
- Fresh database upgrade/downgrade/upgrade: passed. The restored canonical Alembic template and lazy app import allow clean migrations.
- Official frp **v0.71.1**, verified SHA256, binaries outside checkout. `PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /path/to/frp`: real loopback TCP/UDP, native registration, unrelated-port rejection, unchanged-config identity, server reconnect, native-client crash recovery and process/config cleanup passed.
- Actual backend SIGKILL regression passed: owned guard/watchdog/native processes exit and the loopback listener closes.
- Desktop/mobile screenshots use mocked API data; no real router, Aliyun DNS or deployed relay writes were performed.

## Next steps

- Overall coordinator independently reviews the integrated snapshot, shared UI/accessibility fixes and production routing. Its ongoing WIP is retained and not included here.
- Operator supplies frps credentials and optional remote blackbox/webhook settings, then validates from a separate real network. No physical-home/public availability is claimed.
- No push, deployment, paid resource provisioning or real router mapping changes were performed.
