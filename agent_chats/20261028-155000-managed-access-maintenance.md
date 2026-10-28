## Summary

Persist and continuously maintain public services through direct or relay access.

## Changes

- `api/src/app/services/access/`: focused mapping, DNS, health, persistence, reconciliation and background lifecycle modules.
- `api/src/app/models/published_service.py`, `api/src/app/schemas/access.py`, `api/src/app/routers/access.py`: desired configuration, active-admin API and validated evidence.
- `api/src/app/main.py`, `api/src/app/config.py`, `api/.env.example`: lifespan integration and optional relay/probe/webhook settings.
- `api/alembic/env.py`, `api/alembic/script.py.mako`, `api/alembic/versions/f48fc85bcc93_create_published_services.py`: migration metadata/template and published-service table.
- `api/src/app/services/aliyun_dns.py`: complete record pagination and bounded SDK requests, reusing the existing client.
- `api/tests/conftest.py`: shared test-session ownership belongs to fixture teardown, not individual requests.
- `api/tests/test_access_api.py`, `api/tests/test_access_controller.py`, `api/tests/test_access_dns.py`, `api/tests/test_access_health.py`, `api/tests/test_managed_mappings.py`: authorization, persistence, route recovery, probes/alerts and failure regressions.
- `README.md`, `README.zh.md`, `docs/public-access.md`, `tasks.md`: setup, proof boundaries and completed Step 4.

## Outcome

Restore service intent on startup, renew owned mappings, synchronize changed DNS, verify native relay registration, retry and switch automatic routes, retain failed cleanup for retry, and deduplicate failure/recovery webhooks. Historical health expires on restart/stall. Independent probes run concurrently with separate database sessions and cadence is anchored to cycle start.

## Verification

- `pytest -q api/tests/test_access_api.py api/tests/test_access_controller.py`: passed after fixing fixture session ownership and recovery/registration regressions.
- Existing dependencies reused; Python 3.13.5, no dependency additions.
- `python -m alembic revision -m 'create published services'` (in api): initially exposed a missing canonical script template; restored the installed Alembic generic template, reran successfully, then filled migration operations.
- Mandatory hooks and migration upgrade/downgrade/upgrade run in an isolated checkout; no hook skips and no physical router/cloud writes.

## Next steps

Deliver the guided UI and complete final acceptance. Operator configuration is required for a real relay and independent public probe. Only locally validated behavior is claimed; no deployment or push.
