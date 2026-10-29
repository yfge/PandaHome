## Summary

Integrate public relay configuration into PandaHome's existing Public access flow. Users can save the connection, TLS identity verification and optional SSH settings through the administrator API, then enable or pause a published service directly. The current public GPUFree Git relay is preserved while this implementation is reviewed; real App/browser takeover acceptance is pending the integration owner preparing the reviewed deployment.

## Changes

- Added `web/src/components/access/relay-settings.tsx` and `web/src/components/access/relay-settings.test.tsx`: loading, administrator permission feedback, full relay profile GET/PUT, CA/serverName, optional collapsed SSH settings, safe write-only token handling, focused errors, retained failed drafts and retry. Empty password inputs omit token; only explicit removal sends clear_token.
- Updated `web/src/types/access.ts` for the agreed flat relay profile and optional SSH/TLS state metadata; backend contracts remain owned by the integration agent.
- Updated `web/src/components/access/setup-guide.tsx`, `web/src/components/access/network-summary.tsx`, `web/src/i18n/locales/en.json` and `web/src/i18n/locales/zh.json`: actual saved settings replace the environment-only instructions, relay and SSH process state stay distinct from public verification, and the public relay address is distinguished from the PandaHome host's network exit. Cloud frps provisioning remains an operator prerequisite.
- Updated `web/src/components/access/service-card.tsx`, `web/src/app/access/page-client.tsx` and `web/src/app/access/page-client.test.tsx`: direct enable/pause actions use the existing PUT with exactly ServiceDraft fields, disable duplicate mutations while pending, retain real state on errors, and reload after success. Connection settings remain discoverable even if the state request fails. Existing Edit/Delete focus restoration and adjacency are preserved.
- Added this `agent_chats/20261029-044318-relay-settings-ui.md` delivery record. No api/docs/tasks/index/commit changes by this agent. No shared Next.js build output was created.

## Outcome

Web implementation is frozen for the root PM's independent review and integration owner's normal hooks/build. Targeted 50 tests and the complete 121-test web suite pass; lint and TypeScript pass. This is implementation/local verification, not a claim that the persistent GPUFree Git entry has already been adopted by PandaHome or that the real UI acceptance has passed.

## Verification

- `npm run test --prefix web -- src/app/access/page-client.test.tsx src/components/access/relay-settings.test.tsx src/components/access/service-card.test.tsx` — 50/50 passed.
- `npm run test --prefix web` — 121/121 passed in 11 files after the final copy updates.
- `npm run lint --prefix web` — passed.
- `npx --prefix web tsc --project web/tsconfig.json --noEmit --incremental false --pretty false` — passed; no shared build output.
- Product Design index/audit guidance and the project ledger skill were read. Source/contract review is distinguished from screenshot-based UI acceptance; no old/mock images count toward the new real App/browser acceptance.
- Browser/production build/real profile first-save/service cutover — Not run yet; integration owner is preparing a private committed source copy with independent API8033/web3013 and private credentials. Existing standalone SSH/frpc/DNS were not stopped, restarted or changed by this UI implementation.

## Next steps

- Root PM reviews the frozen web diff; the integration owner exclusively stages exact paths, runs normal hooks/build and commits.
- After the reviewed real application is ready, this agent exercises EN/ZH desktop/390px settings, safe credential retention/removal, errors, keyboard navigation, real save/reload and lifecycle controls. Capture and inspect current screenshots in a new private artifact directory.
- Real GPUFree Git cutover needs its own reviewed execution boundary: the old standalone SSH and frpc jobs must both be retired without double-owning ports. Preserve the current DNS exactID and validate public access from the home client. Keep UI state pending when an independent HTTPS probe is unavailable; do not force external_verified.
