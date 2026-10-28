## Summary

Implement both direct and relay public access, automatic network detection and
maintenance, an approachable UI, and sequential atomic commits as requested.

## Changes

- `docs/public-access.md`: design, reused components, ownership and proof boundaries.
- `tasks.md`: Feature 07 acceptance and delivery work state.

## Outcome

Separate candidate direct access from externally verified reachability. Reuse
Aliyun/UPnP services, official frpc and optional Prometheus blackbox exporter;
avoid custom network protocols. Preserve unrelated mappings and credentials.

## Verification

- `pytest -q api/tests`: baseline 35 passed (Python 3.13.5).
- `npm run lint --prefix web`: passed.
- `npm run test --prefix web`: baseline 2 passed.
- `pre-commit install --install-hooks`: installed. No dependencies installed.

## Next steps

Implement Feature 07 in dependency order. Actual public reachability and relay
deployment need operator-supplied network resources; local verification must not
claim field availability. No deployment or push is included.
