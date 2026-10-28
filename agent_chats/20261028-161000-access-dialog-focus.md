## Summary

Resolve independent UI review finding UI-01 for the public-access management flow.

## Changes

- `web/src/app/access/page-client.tsx`: capture initiating buttons explicitly and restore close focus without scrolling; use a stable Add fallback after create/delete.
- `web/src/components/access/service-form.tsx`: expose Radix close-focus handling without changing shared dialog primitives.
- `web/src/components/access/service-card.tsx`: pass typed button events directly to parent actions, avoiding event delegation.
- `web/src/app/access/page-client.test.tsx`: actual keyboard/Radix regressions for EN/ZH add/edit/delete dialogs and close behavior.

## Outcome

Escape/cancel returns focus to the initiating control and preserves position. A successful deletion returns to Add even when its old button no longer exists. This fixes the public-access part of `docs/ue-ui-review.md` UI-01; other domains remain under their owners.

## Verification

- All access/page tests: 37 passed, including 18 new keyboard interaction cases.
- TypeScript, targeted ESLint and whitespace checks passed.
- Mandatory isolated snapshot commit hooks run without skips.

## Next steps

Independent review can replay UI-01 against the final snapshot. Complete shared relay parent-ownership hardening and final local acceptance; no real router writes, deployment or push.
