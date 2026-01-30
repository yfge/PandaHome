## Summary

Completed Feature 06 quality automation: added backend/frontend test tooling, wired tests into pre-commit, and added a GitHub Actions CI workflow.

## Changes

- Backend testing entrypoints + optional deps:
  - `api/pyproject.toml`
  - `scripts/run_api_tests.sh`
- Frontend testing stack (Vitest + React Testing Library) + starter test:
  - `web/package.json`
  - `web/package-lock.json`
  - `web/vitest.config.ts`
  - `web/src/test/setup.ts`
  - `web/src/test/vitest.d.ts`
  - `web/src/components/common/data-state-card.test.tsx`
  - `scripts/run_web_tests.sh`
- Automation:
  - `.pre-commit-config.yaml`
  - `.github/workflows/ci.yml`
- Docs/process:
  - `README.md`
  - `README.zh.md`
  - `agent_chats/README.md`
  - `tasks.md`

## Outcome

- Developers can run `pytest -q api/tests` and `npm run test --prefix web`.
- Pre-commit runs API/web tests when `api/` or `web/` files are staged.
- CI runs lint + tests for both backend and frontend on push/PR.

## Verification

- `ruff check api`
- `pytest -q api/tests` (35 passed; warnings from pytest-asyncio + FastAPI `on_event` deprecation)
- `npm run lint --prefix web`
- `npm run test --prefix web` (Vitest)
- `pre-commit run --hook-stage pre-commit --files .pre-commit-config.yaml .github/workflows/ci.yml scripts/run_api_tests.sh scripts/run_web_tests.sh api/pyproject.toml web/package.json web/package-lock.json web/vitest.config.ts web/src/test/* web/src/components/common/data-state-card.test.tsx README*.md agent_chats/README.md tasks.md agent_chats/20260130-030432-quality-automation-tests-ci.md`

## Next steps

- Consider adding Playwright smoke tests once Feature 06 expands to e2e.
- Optionally address `npm audit` vulnerabilities in a dedicated security-focused PR.
