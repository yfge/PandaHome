## Summary

Independently review and deliver the coordinator's five shared lifecycle and
transport-isolation regressions without changing already delivered runtime code.
The current Access owner has the exclusive shared submission window.

## Changes

- `api/tests/test_lifespan.py`: four cases cover normal reverse-order cleanup,
  partial Access/P2P startup failures and one owner failing during shutdown.
- `api/tests/test_transport_isolation.py`: public relay and private P2P coexist
  under one state root without overwriting credentials/configs or stopping the
  other owner. Both shutdown directions and private restart are exercised.
- This record pairs the previously handed-back tests with independent evidence.

## Outcome

The tests exercise the committed AsyncExitStack startup/cleanup and independent
native-transport ownership contracts. They use explicit fakes for process/cloud
boundaries and disposable SQLite state. They do not claim real frp transfer,
public reachability or cross-NAT traversal; those have separate acceptance layers.
No production source or previous gateway/P2P commit was changed.

## Verification

- Independent `python -m pytest -q api/tests/test_lifespan.py api/tests/test_transport_isolation.py`: **5 passed**.
- Targeted Ruff and `git diff --check`: passed.
- Regular commit hooks run full API regression, with official native frp checks
  enabled by PANDAHOME_FRP_BIN_DIR, without bypass. Final complete counts and
  all-files hooks are recorded in the shared delivery closeout.

## Next steps

This owner incorporates these tests into the current shared stack and completes
remaining setup/documentation delivery. The project manager retains independent
review, with no coding/submission work left assigned to it. Preserve the separate
real-network evidence limits; no deployment, DNS or router mutation is part of
this regression commit.
