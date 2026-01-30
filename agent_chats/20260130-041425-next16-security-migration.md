## Summary

Upgrade frontend dependencies to eliminate `npm audit` vulnerabilities (including the last moderate advisory requiring Next 16) and repair lint/build regressions introduced by the upgrade.

## Changes

- Upgraded Next.js + related deps to Next 16, and aligned i18n + test tooling.
  - `web/package.json`
  - `web/package-lock.json`
- Replaced removed `next lint` with ESLint flat-config and updated hooks.
  - `web/eslint.config.mjs`
  - `scripts/run_web_lint.sh`
  - `.pre-commit-config.yaml`
- Fixed Next 16 build/runtime issues.
  - Wrapped `/login` search params usage behind Suspense by splitting the route into server/client parts:
    - `web/src/app/login/page.tsx`
    - `web/src/app/login/login-client.tsx`
  - Exported missing `ButtonProps` type:
    - `web/src/components/ui/button.tsx`
  - Suppressed new ESLint `react-hooks/set-state-in-effect` warnings where the pattern is intentional:
    - `web/src/app/upnp/page-client.tsx`
    - `web/src/components/domain/record-form-dialog.tsx`
    - `web/src/components/upnp/mapping-form-dialog.tsx`
  - Eliminated `ENVIRONMENT_FALLBACK` errors during `next build` by setting an explicit default timezone for the intl provider:
    - `web/src/components/providers/language-provider.tsx`

## Outcome

- `npm audit --prefix web` reports 0 vulnerabilities.
- `npm run build --prefix web` completes without the previous `ENVIRONMENT_FALLBACK` error noise.

## Verification

- `ruff check api`
- `pytest -q api/tests` (35 passed)
- `npm audit --prefix web` (found 0 vulnerabilities)
- `npm run lint --prefix web`
- `npm run test --prefix web`
- `npm run build --prefix web`
- `pre-commit run --hook-stage pre-commit --all-files`

## Next steps

- Consider consolidating i18n setup (currently both `web/src/i18n/request.ts` and `LanguageProvider` exist) to a single pattern to reduce duplication.
- If desired, stage changes and commit with Conventional Commits + matching `agent_chats` entry.
