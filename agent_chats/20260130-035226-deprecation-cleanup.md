## Summary

Cleaned up test-time deprecation warnings by migrating FastAPI startup/shutdown to Lifespan and modernizing datetime/SQLAlchemy usage.

## Changes

- Replaced `@app.on_event` startup/shutdown with FastAPI Lifespan; skip UPnP discovery during pytest:
  - `api/src/app/main.py`
  - `api/tests/conftest.py`
- Removed deprecated `datetime.utcnow()` usage when creating JWTs:
  - `api/src/app/auth/auth.py`
- Updated SQLAlchemy base import to `sqlalchemy.orm.declarative_base`:
  - `api/src/app/database/database.py`
- Silenced pytest-asyncio loop-scope warning via explicit config:
  - `api/pyproject.toml`

## Outcome

- `pytest -q api/tests` runs cleanly without the previously observed deprecation warnings.

## Verification

- `ruff check api`
- `pytest -q api/tests` (35 passed)
- `npm run lint --prefix web`
- `npm run test --prefix web` (Vitest)

## Next steps

- Optional: address the Vitest/Vite “CJS build of Vite's Node API is deprecated” warning (non-blocking).
