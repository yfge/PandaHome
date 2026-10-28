## Summary

The independent UE/UI reviewer found that English pages retained a Chinese HTML
language tag, affecting assistive technology language selection (UI-02).

## Changes

- `web/src/components/providers/language-provider.tsx`: synchronize the document
  language after locale changes.
- `web/src/components/providers/language-provider.test.tsx`: verify both switch
  directions and the persisted language after reopening the page.

## Outcome

Visible English/Chinese content and the root language tag agree. This follows the
existing client-side language selection without introducing locale-prefixed URLs.

## Verification

- `npm run test --prefix web -- src/components/providers/language-provider.test.tsx`:
  two passed.
- Independent current-run browser verification: EN to ZH to EN with refresh
  restored the expected language, page content and saved preference. Evidence:
  `ue-ui-review/language-recheck.json` and
  `ue-ui-review/49-english-language-after-fix.png` under the coordinator's
  visualization directory.

## Next steps

Independent final production verification covered immediate menu switching and
refresh in EN/ZH; the final reviewer evidence is linked from docs/ue-ui-review.md.
The current owner independently reran both tests, TypeScript and ESLint before
this atomic handoff. No full screen-reader compliance claim is made.
