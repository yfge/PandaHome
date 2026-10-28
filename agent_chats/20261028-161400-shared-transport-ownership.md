## Summary

Unify public and private frp process ownership across abrupt backend/monitor death.

## Changes

- `api/src/app/services/process_guard.py`: coordinator-developed shared guard/watchdog with immutable process identity and owned process-group cleanup.
- `api/src/app/services/relay.py`: all native transports use the canonical guarded command.
- `api/src/app/services/p2p.py`: remove its redundant command wrapper and imports; other P2P work preserved.
- `api/tests/test_process_guard.py`: coordinator-owned real lifecycle tests, included with the shared implementation as one coherent prerequisite.
- `api/tests/test_relay.py`, `api/tests/test_p2p_service.py`: public backend-death coverage and shared command identity expectations.
- `api/tests/integration/frp_smoke.py`: distinguish native frpc from its guard and crash the native client for recovery verification.

## Outcome

Reuse one guard rather than duplicate supervision. Backend, outer guard, watchdog and native identities remain distinct; old/foreign PIDs are never treated as owned merely by number. Group cleanup is POSIX-specific. This common integration commit includes the implementation and its consumers together; unrelated P2P/UI/docs work remains outside it.

## Verification

- Related public relay/status/P2P/guard suite: 85 passed.
- Real public-relay backend SIGKILL test: owned processes disappear and loopback listener closes.
- Official frp v0.71.1 loopback smoke: TCP/UDP, native registration, occupied-port rejection, native reconnect and native-client crash recovery passed.
- Mandatory isolated snapshot hooks run without skips. Full integrated acceptance follows this shared prerequisite.

## Next steps

Close Feature 07 local acceptance and hand the final snapshot to independent overall review. No physical router/cloud writes, deployment or push.
