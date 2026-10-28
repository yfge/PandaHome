## Summary

Fix two test-only assumptions exposed by a fresh dependency install and a source
snapshot without Git metadata. Preserve public gateway and relay behavior without
changing production code, pinning pytest or accessing Starlette State internals.

## Changes

- `api/tests/test_upnp_gateway.py`: the `routers` fixture explicitly saves the
  current `app.state.upnp_service`, assigns its fake service, yields, and restores
  the previous service in `finally`. Module-level factory mocking remains intact;
  pytest's monkeypatch undo no longer manages the Starlette State attribute.
- `api/tests/test_relay.py`: `test_state_inside_checkout_is_rejected` creates a
  temporary checkout with `.git` and a fake service source file, then points the
  relay module's `__file__` at it. The real constructor still rejects private relay
  state within that checkout, independent of actual snapshot metadata.
- `agent_chats/20261028-171413-clean-setup-test-boundaries.md`: focused scope,
  verification and clean-environment handoff record.

## Outcome

Both targeted test files pass in the existing base environment: 54 tests passed.
The changes preserve fixture restoration and exercise the real checkout guard.
No production implementation, dependency range, system SDK, credentials or shared
index was modified by this agent. The clean-setup owner has been notified to copy
these two files into its isolated source snapshot and rerun the fresh pytest 9.2
environment; that result is tracked separately.

## Verification

- `python -m pytest api/tests/test_upnp_gateway.py api/tests/test_relay.py -q`:
  54 passed in 5.81 seconds with Python 3.13.5 and pytest 8.3.3 in the existing
  base environment.
- `ruff check api/tests/test_upnp_gateway.py api/tests/test_relay.py`: passed.
- `git diff --check -- api/tests/test_upnp_gateway.py api/tests/test_relay.py`:
  passed.
- Fresh-install pytest 9.2 rerun: Not run by this agent; the network-detection
  owner is refreshing its isolated snapshot and owns that verification.
- Whole-repository checks and commit: Not run by this agent; the root coordinator
  owns final validation, staging and commits.

## Next steps

Clean-setup owner: refresh only the two named test files and rerun the fresh
environment's test suite. Root coordinator: review those results and include these
minimal compatibility changes with this log in the appropriate atomic commit.
Keep unrelated parallel work unchanged; this agent performs no staging or commit.
