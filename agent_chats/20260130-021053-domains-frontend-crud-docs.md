## Summary

Completed Feature 04 frontend domain record CRUD flow and added Aliyun DNS setup documentation.

## Changes

- Added record CRUD dialogs + optimistic updates:
  - `web/src/components/domain/record-list.tsx`
  - `web/src/components/domain/record-form-dialog.tsx`
  - `web/src/components/domain/record-delete-dialog.tsx`
- Protected domain records route:
  - `web/src/app/domains/[domain]/records/page.tsx`
- Added domain workflow strings:
  - `web/src/i18n/locales/en.json`
  - `web/src/i18n/locales/zh.json`
- Added Aliyun setup guide + linked from READMEs:
  - `docs/domains.md`
  - `README.md`
  - `README.zh.md`
- Marked Feature 04 steps complete:
  - `tasks.md`

## Outcome

- Domains records page now supports add/edit/delete with inline validation and toast feedback.
- Documentation now describes required Aliyun env vars, permissions, and rate-limit troubleshooting.

## Verification

- `npm run lint --prefix web`
- `ruff check api`
- `pytest -q` (32 passed; warnings from pytest-asyncio + FastAPI `on_event` deprecation)
- `pre-commit run --hook-stage pre-commit --files README.md README.zh.md tasks.md docs/domains.md web/src/components/domain/* web/src/app/domains/[domain]/records/page.tsx web/src/i18n/locales/* agent_chats/20260130-021053-domains-frontend-crud-docs.md`

## Next steps

- Consider adding backend support for creating/removing domains if needed (README endpoints were updated to match current API).
- Add a small e2e smoke test (Playwright) once Feature 06 testing stack is introduced.
