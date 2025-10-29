## Summary
- Added the `/api/auth/token` endpoint and tightened user management RBAC using dependency-injected helpers.

## Changes
- Created `api/src/app/routers/auth.py` with a password-grant login handler wired to shared auth settings.
- Updated `api/src/app/auth/auth.py` with a reusable `require_role` dependency and linked helpers.
- Normalized auth configuration defaults and parsing (`api/src/app/config.py`, `api/src/app/auth/dependencies.py`, `api/.env.example`).
- Cleaned up the users router paths and role requirements (`api/src/app/routers/users.py`), refreshed docs, and ticked Feature 02 Step 2 in `tasks.md`.

## Outcome
- Clients can now obtain bearer tokens via `/api/auth/token`, and admin-only user endpoints enforce RBAC consistently.

## Verification
- `python3 -m compileall api/src`

## Next steps
- Proceed to Feature 02 Step 3 (user migration + admin bootstrap).
