## Summary
- Bootstrapped Alembic migrations for the users table and added a CLI to seed the first admin account.

## Changes
- Added Alembic configuration (`api/alembic.ini`, `api/alembic/env.py`) and initial migration `20251029_01_create_users_table.py` reflecting the SQLAlchemy `User` model.
- Introduced `bootstrap-admin` console script (`api/src/app/cli/bootstrap_admin.py`, `api/pyproject.toml`) to create or update an admin user with hashed credentials.
- Updated auth settings parsing, defaults, and documentation to support the migration/CLI workflow, and marked Feature 02 Step 3 complete (`api/src/app/config.py`, `api/src/app/auth/dependencies.py`, READMEs, `.env` example, `tasks.md`).

## Outcome
- Database schema is now managed via Alembic, and developers have a documented path to seed an administrator account after running migrations.

## Verification
- `python3 -m compileall api/src`

## Next steps
- Move to Feature 02 Step 4: add pytest coverage for token issuance and user CRUD.
