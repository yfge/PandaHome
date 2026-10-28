## Summary

Detect public IPv4, upstream NAT, CGNAT and missing evidence without opening ports.

## Changes

- `api/src/app/services/network_detection.py` and `api/src/app/schemas/network.py`: bounded read-only IPv4 evidence and conservative recommendations.
- `api/src/app/services/upnp.py`: independent WAN IP read, exact gateway host matching and reusable managed-action/cache interfaces.
- `api/tests/test_network_detection.py`: classifications, bounded fallback/error behavior, cancellation and exact gateway targeting.
- `tasks.md`: complete Feature 07 Step 2.

## Outcome

A matching global WAN/observed IP is only a direct candidate. No router mapping was created. This isolated checkout avoids stashing parallel gateway/P2P work in the shared checkout.

## Verification

- `PYTHONPATH=api pytest -q api/tests`: run by mandatory commit hooks against this isolated staged snapshot.
- `pre-commit`: mandatory hooks run without skips; original Python 3.13.5 dependencies reused. No installation required.

## Next steps

Integrate frp and persisted automatic maintenance. Router/public reachability remains a separate deployment check.
