## Summary

Implemented the `/api/status` system metrics endpoint (CPU/memory/disk/services), extended `/health`, and completed the monitoring dashboard + docs.

## Changes

- Backend status contract + cached metrics service:
  - `api/src/app/schemas/status.py`
  - `api/src/app/services/status.py`
  - `api/src/app/routers/status.py`
  - `api/src/app/main.py`
- Added `psutil` dependency:
  - `api/pyproject.toml`
- Added pytest coverage for `/api/status` + `/health`:
  - `api/tests/test_status.py`
- Added refresh interval controls on the status page:
  - `web/src/components/server/status.tsx`
- Filled missing status i18n strings:
  - `web/src/i18n/locales/en.json`
  - `web/src/i18n/locales/zh.json`
- Added monitoring documentation and linked from READMEs:
  - `docs/monitoring.md`
  - `README.md`
  - `README.zh.md`
- Marked Feature 05 steps complete:
  - `tasks.md`
- Ignored local SQLite file created by default DB URL:
  - `.gitignore`

## Outcome

- `/api/status` returns a cached status snapshot compatible with the existing Next.js status page.
- Status page supports configurable auto-refresh + manual refresh.
- Monitoring docs explain data sources, caching, and troubleshooting.

## Verification

- `pip install -e api` (installed `psutil`)
- `ruff check api`
- `pytest -q` (35 passed; warnings from pytest-asyncio + FastAPI `on_event` deprecation)
- `npm run lint --prefix web`
- `pre-commit run --hook-stage pre-commit --files api/pyproject.toml api/src/app/** api/tests/test_status.py web/src/components/server/status.tsx web/src/i18n/locales/* docs/monitoring.md README*.md tasks.md agent_chats/20260130-022533-status-endpoint-monitoring.md`

## Next steps

- Consider moving FastAPI startup/shutdown handlers to a Lifespan handler (FastAPI `on_event` deprecation warning).
- Add process-based service checks (systemd/Docker) if PandaHome needs to monitor real daemons beyond in-process state.
