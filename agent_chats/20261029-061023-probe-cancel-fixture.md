## Summary

Separate the external SSH probe's deliberate cancellation regression from the timeout regression after independent review reproduced a cold-start fixture failure. This is a test-only correction; production probe deadlines and lifecycle code remain frozen.

## Changes

- `api/tests/test_ssh_probe.py`: the cancellation case keeps a ten-second probe budget, waits for actual native readiness under a separate five-second startup deadline, and only then actively cancels. The timeout case retains its real one-second deadline. Both retain the real native/watchdog/guard cleanup assertions. A final cleanup block also reaps the test task if readiness assertions fail.
- `agent_chats/20261029-061023-probe-cancel-fixture.md`: record the independent failure and narrow correction without altering prior evidence or the first frozen implementation log.

## Outcome

The independent failure was a fixture timing collision: the one-second deadline expired during cold interpreter/guard startup, before the cancellation branch could begin. Production code was not changed or its assertions weakened. All seven product/config files match the original `ssh-probe-freeze.json` SHA values; only this new log and the test file differ. No staging, commit, deployment or external probe was performed by this agent.

## Verification

- Original independent result retained at the automatic-probe run's `integration-independent-guard-tests.log`: 1 failed / 5 passed. The cancellation case returned the correctly conservative false on deadline, rather than reaching the intended active-cancel scenario. Original freeze and raw failure files remain unchanged.
- `PYTHONPATH=api python -m pytest -q api/tests/test_ssh_probe.py -k 'timeout_and_cancellation or short_native or killed_watchdog or backend_sigkill'`: 6 passed, 23 deselected in 4.45s; exit 0.
- Targeted Ruff and `git diff --check`: passed.
- Full unchanged product/native suites: Not rerun because this correction changes only test timing and test teardown. The integration owner runs required normal hooks.

## Next steps

- Publish a separate v2 freeze manifest, preserving the original freeze and failure evidence, for PM and independent owner review.
- Integration owner alone stages and commits with normal hooks. Product deployment remains contingent on that review and normal field acceptance.
