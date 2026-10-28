# Guard force-kill and process identity review

## Summary

The integration reviewer requested adversarial checks for direct guard SIGKILL,
FrpRelay's forced-kill stop path and PID reuse. The first P2P-only guard handled
backend death and normal SIGTERM, but could leave its native child after the
guard itself was killed. Public relay needs the same protection.

## Changes

- `api/src/app/services/process_guard.py`: add a shared `guarded_command` entry
  point with the backend PID and pre-spawn creation time. The tracked guard G
  launches watchdog W in its own POSIX session; W alone creates frpc and checks
  immutable backend/G identities. G kills W's owned process group before reaping
  its leader, so a watchdog crash cannot orphan a child or reuse the group ID.
- `api/src/app/services/p2p.py`: use the shared relay startup contract rather
  than adding a second P2P wrapper. `api/tests/test_p2p_service.py` verifies the
  shared command's stable parent identity and lack of credential arguments.
- `api/tests/test_process_guard.py`: real Python/loopback TCP regressions for
  normal TERM, backend/G/W SIGKILL, mismatched parent creation time, ignored TERM,
  startup interruption, forced stop, command identity and wrapper idempotence.
  Concurrent services verify group-cleanup isolation. Inherited SIGCHLD ignore
  is reset before spawning children so their leader cannot be auto-reaped early.
- `docs/p2p.md`, `tasks.md`: document process topology, bounded cleanup and
  single-monitor-loss acceptance without claiming cross-network traversal.
  The backend handoff adds a standalone process-regression command to
  `docs/p2p.md`; it needs no frp binary or physical router.
- Access owns the coordinated adoption in `api/src/app/services/relay.py`,
  `api/tests/test_relay.py` and `api/tests/integration/frp_smoke.py`.

## Outcome

The shared helper covers an individual guard, watchdog or backend disappearing.
Normal SIGTERM allows native cleanup; a frozen guard forcibly killed by relay's
stop timeout leaves the watchdog to close the native TCP listener. PID plus
creation-time checks prevent a recycled bare PID from standing in for the owner.
The P2P adapter has no additional guard layer after Access adopts the helper.
The coordinated implementation and its consumers/tests were committed together
by Access as `2e440ad` (`fix(runtime): unify guarded ownership of native transports`).
This follow-up retains the review evidence, operational contract and task state.

This is POSIX/local process evidence. If every monitor is killed together while
the native process is left alive, an external service supervisor must clean the
whole process tree. Native cleanup is bounded and depends on surviving monitors
being scheduled; it is not an instantaneous revocation guarantee.

## Verification

- `python -m pytest -q api/tests/test_process_guard.py`: 12 passed in 5.29 s,
  including a real forced-kill path using SIGSTOP + `_STOP_TIMEOUT=0.05`, separate
  service isolation and a backend with inherited `SIGCHLD=SIG_IGN`.
- `python -m pytest -q api/tests/test_process_guard.py api/tests/test_p2p_service.py`:
  initial combined 38 passed; no router or cloud endpoint participates.
- `PANDAHOME_FRP_BIN_DIR=/path/to/verified/frp python -m pytest -q api/tests/test_p2p_native.py`:
  4 passed in 14.93 s with official SHA256-verified frp 0.71.1. This remains
  loopback XTCP/STCP/backend-death evidence, not real cross-NAT traversal.
- `python -m pytest -q api/tests/test_process_guard.py api/tests/test_p2p_service.py
  api/tests/test_relay.py api/tests/test_transport_isolation.py`: 63 passed before
  the final inherited-SIGCHLD parameter; the complete guard suite passed after it.
- Full API regression before the final inherited-SIGCHLD parameter: 362 passed,
  4 optional native tests skipped; those 4 passed separately with real binaries.
- Targeted `pre-commit run --files` across helper, shared relay, P2P adapter,
  their tests, documentation, task state and this log: passed, including full API
  regression, Python lint and the collaboration-log check. No hooks were bypassed.

### Final backend handoff recheck

- `python -m pytest -q api/tests/test_process_guard.py api/tests/test_p2p_service.py
  api/tests/test_relay.py api/tests/test_transport_isolation.py`: 65 passed in
  10.66 s. Independent read-only review found no new required fix and confirmed
  that P2P inherits the base relay's single guard wrapper.
- `PANDAHOME_FRP_BIN_DIR=/path/to/verified/frp python -m pytest -q api/tests/test_p2p_native.py`:
  4 passed in 14.40 s, still limited to local XTCP/STCP/revocation/recovery.
- `python -m pytest -q api/tests`: 364 passed, 4 optional native tests skipped
  in 27.82 s on the current shared worktree. The native tests passed separately
  above. This snapshot includes integration/Access-owned test work, which this
  handoff neither modifies nor stages.
- Documentation was independently checked against the shared implementation,
  including the process-group identity and complete-monitor-loss boundaries.

## Next steps

The shared Access/P2P backend commit is complete in `2e440ad`; the initial guard
acceptance record is in `3e6bde2`. This follow-up commits only `docs/p2p.md` and
this backend log. No uncommitted backend implementation remains with the P2P
owner. The PM exclusively owns P2P's four frontend components/tests and their
separate UX log/commit; do not modify or stage them or their task-state WIP.
Let the overall reviewer run the final integrated UI/transport snapshot after
other owners finish. Keep the real cross-NAT task open. Do not push, deploy or
modify real routers; preserve all integration/Access/UI reviewers' unrelated WIP.
