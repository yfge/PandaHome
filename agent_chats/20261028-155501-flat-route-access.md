# Preserve flat application routes

## Summary

Actual browser review of the production P2P page found that the existing
next-intl middleware redirected `/p2p` to `/en/p2p`, which returned 404. The
repository has flat app routes and a client-side LanguageProvider rather than
an `app/[locale]` route hierarchy.

## Changes

- `web/middleware.ts`: remove the incompatible locale-routing middleware.
  Existing client-side Chinese/English selection remains in LanguageProvider.

## Outcome

PandaHome's flat page URLs can be served directly instead of being rewritten to
an absent language-prefixed subtree. This is a separate runtime prerequisite
identified during P2P acceptance, not a change to P2P transport behavior.

## Verification

- Before the fix, the production browser redirected `/p2p` to `/en/p2p` and
  rendered 404 before any P2P API request.
- `npm run build` in `web/`: passed after middleware removal.
- Production HTTP checks: `/p2p`, `/access` and `/login` each returned 200 at
  the requested flat URL, with no locale-prefix redirect.
- Isolated real headless Chrome UI review: desktop 1440x1000 and mobile
  375x812 passed without document/body horizontal overflow; the open service
  form's inputs have labels and remain within the mobile viewport.
- API responses were intercepted (fake admin plus a setup-needed P2P service);
  this is UI/routing evidence only. Screenshots are temporary artifacts at
  `/tmp/pandahome-p2p-desktop.png` and `/tmp/pandahome-p2p-mobile.png`.

## Next steps

Retain language switching within the existing provider. API calls in the UI
preview are intercepted test responses; the preview does not establish any live
tunnel or network acceptance evidence. The isolated browser was closed after
review and the temporary production preview will be stopped before handoff.
