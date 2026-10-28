## Summary

Close the rapid-keyboard focus gap in Access dialogs and keep new validation or
save errors inside the current form. The initial coordinator request withheld staging while other owners used the
index. The latest unified closeout instruction supersedes that hold and assigns
this owner the exclusive atomic-commit window.

## Changes

- `web/src/app/access/page-client.tsx`: restore Add/Edit/Delete triggers during
  the closing layout commit, before another keyboard event. Suppress Radix's
  delayed close autofocus so it cannot steal a subsequent Tab. Unmount the closed
  delete dialog, matching the service form, so its old focus trap cannot refocus
  a still-connected Cancel button. Preserve the stable Add fallback after removal.
- `web/src/components/access/service-form.tsx`: make the inline alert focusable;
  focus new validation and request errors with separate effects. Clearing a
  validation error must not refocus an unchanged server error while the user types.
- `web/src/app/access/page-client.test.tsx`: synchronous Escape regressions for
  Add/Edit/Delete, continued Tab/Shift-Tab, late-callback stability, failed save,
  retained drafts and successful retry in English and Chinese.
- `web/src/components/access/service-form.test.tsx`: verify focused validation
  feedback and uninterrupted full input after an earlier server error.

## Outcome

The previous `521eea8` fix restored focus eventually, but real Chrome traced an
approximately 11 ms gap after unmount: BODY received focus, Tab reached Home,
and the delayed callback pulled it back to Add. The new synchronous close tests
failed in all four Add/Edit locale cases before this change. Separate regression
also reproduced the stale-error bug by retaining only the first typed character.
Both behavior gaps are now covered and fixed. Independent final read-only review
found no remaining blocker in these four files.

The public relay P1 is already implemented by shared Access/P2P commit `2e440ad`,
with same-state/same-proxy/same-port backend-SIGKILL restart proof in `9fe7623`.
This round reran its real process and native-frp checks; no duplicate supervisor
or backend change was needed.

## Verification

- `npm run test -- src/app/access/page-client.test.tsx src/components/access/service-form.test.tsx` from `web/`: **42 passed**.
- Final `npm run test` from `web/`: **91 passed**; `npm run lint`: passed.
- `npx tsc --noEmit --incremental false`: passed; final isolated `npm run build` also passed TypeScript and all 11 generated pages. Dependencies were copied with APFS clone into a private source snapshot; shared `.next` and environment files were not used or changed.
- Actual production Next page in an isolated Chrome/profile, EN/ZH x 390/1440: **88 state records passed**. Covers immediate Escape-to-Tab, late focus stability, Add/Edit failure and retry, full correction after validation with a stale server error, plus Delete-to-Shift-Tab. APIs were intercepted by the existing reviewer mock; no real router/DNS/relay operation was called by the browser.
- Browser results, replay, screenshots and source fingerprints: `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-focus-followup/`. The two mobile failure screenshots were reopened and visually checked after the final production run.
- `PYTHONPATH=api pytest -q api/tests/test_process_guard.py api/tests/test_relay.py`: **34 passed**, including backend/guard/watchdog death and two-generation public relay restart.
- `PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /var/folders/rc/ffg_cryd6jsbjc2srvhbqnc40000gn/T/pandahome-frp-smoke-u00bqj7x/frp_0.71.1_darwin_arm64`: **passed**; actual native frpc crash, registration, TCP/UDP recovery, conflicts and cleanup all verified on loopback.
- `git diff --check`: passed. The regular atomic commit runs every applicable mandatory hook without bypass.
  Final all-files hooks are recorded in the shared delivery closeout. Own preview and Chrome processes were stopped.

## Next steps

This owner commits the four Access files and this record now, then supplies the
hash for independent affected UE/UI verification before the final shared docs
acceptance. The same owner delivers the remaining shared work; the project
manager remains a coordinator/reviewer. Preserve all existing gateway/P2P/main
commits. No push, deployment or router write is authorized by this UI correction.
The browser uses mocked APIs; native frp checks establish loopback/process proof,
not real cross-network availability. The separately authorized real DDNS update
P1 is delivered as e2e4b22 with its own owned-resource cleanup evidence.
