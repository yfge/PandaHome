## Summary

Explain the actionable missing relay setup for a detected NAT network.

## Changes

- `api/src/app/services/access/reconcile.py`: CGNAT/upstream NAT with no relay reports `relay_not_configured`, while genuinely incomplete network evidence remains `network_unknown`.
- `api/tests/test_access_controller.py`: require the missing-relay guidance for detected CGNAT.

## Outcome

The service card gives the setup instruction that matches the known network instead of asking the user to repeat detection unnecessarily.

## Verification

- Final isolated integrated snapshot: `PYTHONPATH=api pytest -q api/tests`: 346 passed, 4 optional native-P2P tests skipped.
- `npm run test --prefix web`: 42 passed. `npm run lint --prefix web`: passed.
- `npm run build --prefix web`: passed with coordinator-owned Next16 params/login fixes included unstaged solely for combined acceptance; those shared fixes are not part of this commit.
- Mandatory commit hooks run without skips.

## Next steps

Fix the independently reported public-access dialog focus restoration issue, then close Feature 07 local acceptance. Real home/public connectivity remains untested and no deployment/push/router writes occurred.
