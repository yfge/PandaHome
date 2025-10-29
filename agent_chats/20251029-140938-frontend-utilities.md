## Summary
- Added shared frontend utilities, including Tailwind-friendly class merging and a typed API client.

## Changes
- Created `web/src/lib/utils/cn.ts` with a `cn` helper (re-exported via `web/src/lib/utils/index.ts`) to satisfy `@/lib/utils` imports.
- Introduced `web/src/lib/api-client.ts` that wraps `fetch`, serializes JSON bodies, and raises typed errors while respecting `NEXT_PUBLIC_API_BASE_URL`.
- Updated `.gitignore` so the new `web/src/lib/**` directory is tracked.
- Checked off Feature 01 Step 4 in `tasks.md` to reflect completion.

## Outcome
- React components can now import `cn` without build errors, and upcoming refactors can reuse the centralized API client.

## Verification
- `npm run lint --prefix web` *(fails: existing lint violations in domain/record-list useEffect deps and language-provider explicit any; unchanged in this task)*

## Next steps
- Address lint failures while refactoring fetch logic in Feature 01 Step 5.
