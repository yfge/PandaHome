## Summary
- Centralized backend configuration defaults in `Settings` for database, auth, and Aliyun parameters.

## Changes
- Replaced `api/src/app/config.py` with a `BaseSettings` implementation that loads `.env` from the `api/` root and exposes defaults for `SECRET_KEY`, `DATABASE_URL`, and `ALIYUN_REGION_ID`.
- Refactored `api/src/app/auth/auth.py`, `api/src/app/database/database.py`, and `api/src/app/services/aliyun_dns.py` to consume the shared `settings` values instead of hard-coded constants.
- Cleaned up `api/src/app/main.py` import list and marked Feature 01 Step 3 as complete in `tasks.md`.

## Outcome
- Secrets and connection settings now pull from a single source, enabling consistent overrides via environment variables or `.env`.

## Verification
- `python3 -m compileall api/src`

## Next steps
- Advance to Feature 01 Step 4 (frontend utilities).
