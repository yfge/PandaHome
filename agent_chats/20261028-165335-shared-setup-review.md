## Summary

Review the shared setup documentation without changing database defaults, running migrations, or modifying application behavior.

## Changes

- `README.md` and `README.zh.md`: describe a virtual environment and `api[test]` dependencies, align Next.js 16 and hook descriptions with the repository, and separate the backend `api/` terminal from the frontend repository-root terminal.
- `README.md` and `README.zh.md`: explain that `sqlite:///./app.db` is relative to the current working directory; migrations, administrator bootstrap, and `uvicorn src.app.main:app --port 8003` must use the same `api/` working directory. Correct the hashing-scheme JSON-array setting and clarify optional Aliyun credentials.
- `AGENTS.md`: fix case-sensitive handbook references, document the same database/startup convention and actual test hooks, and use the correct UPnP delete route parameter.
- `CLAUDE.md`: link to canonical `AGENTS.md` and mirror the shared setup and verification reminders.
- Root owner additions after independent clean-install findings: `api/.env.example` uses a JSON hashing list; `api/pyproject.toml` declares the email validator extra and HTTP test client, and bounds bcrypt below 5 for existing Passlib compatibility. No hashing algorithm or database default changed.
- `docs/auth-lifecycle.md`: use the same explicit api working directory and current protected-route list. `docs/backend-dependency-audit.md`: replace historical pending dependency actions with current requirements and the independently verified process-only macOS SDK override.
- `README.md` and `README.zh.md`: link the host-specific native build note and identify all current protected pages. Separate test-compatibility and fresh-install logs accompany this setup unit.

## Outcome

The bilingual setup instructions now use one explicit database location while preserving the configured relative SQLite URL. No database was migrated, moved, or bootstrapped. Existing shared changes were preserved; staging and committing remain owned by the root agent.

## Verification

- `git diff --check -- README.md README.zh.md AGENTS.md CLAUDE.md`: passed.
- Read `web/package.json`, the installed Next.js package engine requirement, `api/pyproject.toml`, Alembic configuration, bootstrap CLI, and the pre-commit scripts to check command and dependency descriptions.
- A read-only Markdown check verified balanced code fences, existing relative link targets, Next.js 16 agreement, the API startup command, and SQLite working-directory guidance.
- `Settings(_env_file='api/.env.example')` reproduced the pre-existing invalid `AUTH_HASHING_SCHEMES=bcrypt` template value. Reported the required JSON-array correction to the root agent.
- The initial documentation-only subtask ran no migrations/bootstrap/server. The root owner then independently delegated a clean Python 3.13 venv install of an isolated source copy, without system-site-packages: editable `api[test]` installation, `pip check`, environment parsing, application hash/verify, TestClient requests and netifaces runtime probes all passed.
- Clean default macOS SDK27 selection first failed its linker probes; selecting the already installed SDK26.5 for only the pip process built the unmodified netifaces sdist. No system SDK/compiler changes or persistent config were made. Durable diagnosis: `setup-toolchain-20261028/` under the Access visualization root.
- Full fixed-copy backend test suite with freshly resolved dependencies and pytest 9.2: **369 passed, 4 optional native tests skipped**. The two isolated test-boundary fixes have their own log; current main-environment native verification is separate.
- Actual operator databases, users and application credentials were not migrated, moved, reset or bootstrapped. All fresh probes/test databases were disposable.

## Next steps

The current Access delivery owner commits the complete reviewed setup unit with
its environment/metadata/test fixes and independent logs, then runs the latest
shared production/type/lint/tests/all-files hooks. No setup coding or commit is
left to the project manager. Physical network/deployment acceptance remains a
separate operator environment step, not a missing local installation change.
