## Summary
- Extracted reusable auth settings and helpers, enabling dependency injection for password hashing and token issuance.

## Changes
- Added `api/src/app/auth/dependencies.py` to expose cached `AuthSettings`, password context, and OAuth2 scheme builders.
- Updated `api/src/app/auth/auth.py` to consume the new helpers, remove module-level singletons, and accept injected settings.
- Expanded `api/src/app/config.py` with hashing/token configuration fields and mirrored them in `api/.env.example` and README tables.
- Documented new environment options in both README files and marked Feature 02 Step 1 as complete in `tasks.md`.

## Outcome
- Authentication flows now draw configuration from a single settings source, and FastAPI routes can inject auth dependencies cleanly.

## Verification
- `python3 -m compileall api/src`

## Next steps
- Continue with Feature 02 Step 2 to flesh out the `/api/auth/token` endpoint and RBAC enforcement.
