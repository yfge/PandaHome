## Summary

Privately fix the independently confirmed pending Edit503 menu-close P2 on
`e8be058`. After a held write and dialog Escape, the user can leave the disabled
menu and Tab to real Home. When the request fails and its button re-enables, the
outer DropdownMenu's delayed close-autofocus steals Home focus at animation end.
The existing dialog pending-focus guard already respects that Home focus.

The Access owner exclusively owns shared index/review/application/commit work.
This task remains private preparation; no shared path is written or staged.

## Changes

- `web/src/components/upnp/mapping-list.tsx`: add only an UPnP DropdownMenuContent
  close-autofocus handler. If focus has moved to a genuine element outside that
  closing menu, prevent Radix's delayed return. BODY and Radix focus-guard states
  retain the default restoration. No shared menu primitive, dialog lifecycle,
  request/ownership, backend, locale, design or API changes.
- `web/src/components/upnp/mapping-list.test.tsx`: extend the existing tracked
  test file with two held Edit/Delete503 menu-animation/outside-focus regressions
  and a normal menu Escape-to-Actions control. All earlier tests remain.
- `agent_chats/20261028-174135-upnp-pending-menu-focus.md`: independent UTC private-candidate log and handoff evidence.

## Outcome

**Private candidate ready for Access review and precise application.**
Private copy: `/var/folders/rc/ffg_cryd6jsbjc2srvhbqnc40000gn/T/pandahome-upnp-menu-2ba91rg2`.
Base commit: `e8be058f59c03a6990730481be77d06777274a95`.
The source baseline still hashes to
`55e5ae736126a6d07be06eb133b206b9160950696c7aeff6eecac645894acc6d` in
the shared tree. Only the private mapping-list and its tracked test plus this
new private log differ. No shared source, index, staging, commit, build or docs
were touched. Temporary browser/fixture processes were stopped after validation.

The guard preserves actual user navigation, including Home during a closing
menu's animation and after its trigger becomes enabled. It does not change the
accepted Edit/Delete -> original menu item -> Escape -> Actions contract. This
also avoids default-focus scrolling when a user already chose another element.

## Verification

- Inspected installed Radix DropdownMenuContent: default onCloseAutoFocus focuses
  its trigger unless the event is prevented. The original dialog pending guard
  is separate and already checks current activeElement.
- New regression baseline: both Edit and Delete tests failed after a real Radix
  menu's modeled exit animation completed; focus moved from Home to Actions.
  The ordinary Escape-to-Actions control passed. Test baseline output is retained
  locally with the candidate evidence.
- Native Chrome baseline: **2/2 EN390 pending Edit503 cases reproduced** the
  independent defect. Real key events close the form, exit the disabled menu,
  Tab to a visible Home link and only then release the held DELETE503. Evidence:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-pending-menu-20261028-174135/baseline/pending-results.json`.
- Private focused command inside `web/`:
  `npm run test -- src/components/upnp/mapping-list.test.tsx src/components/upnp/gateway-manager.test.tsx`:
  **30 passed** (24 mapping-dialog/menu tests plus 6 existing gateway tests).
  This retains all stable-close, rapid-close, disabled pending, error/draft,
  corrected-validation, retry, last-row fallback and gateway tests.
- `npx tsc --noEmit --incremental false`: passed.
- `npm run lint`: passed in the private copy.
- Native pending matrix: **16/16 passed**, EN/ZH x 390/1440 x Edit/Delete x
  continued Home navigation/no-navigation controls. The 8 Home paths retain
  genuine Home focus at release+40ms and +350ms with unchanged chosen scroll
  position; no focus guard is mistaken for Home. The 8 no-navigation controls
  restore their original enabled menu item; Escape then returns to Actions.
  At +40ms a no-navigation control may still be busy and neutral; it is not
  required to restore a disabled entry before its asynchronous failure settles.
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-pending-menu-20261028-174135/fixed/pending-results.json` records exact snapshots, keys and
  requests. All writes use the explicit second gateway and are mocked.
- Native EN/ZH390 add/edit/delete inline 503 visibility/focus, complete drafts,
  corrected validation, retries and deleted-row fallback passed again, using
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-pending-menu-20261028-174135/errors/submit-error-evidence.json`. No browser runtime exceptions.
- The already accepted 48-case rapid-close production matrix is not rerun here;
  the earlier rapid-close unit regressions remain in the focused suite. Full
  product build/all-tests/hooks: Not run – Access owns final gates and this
  phase does not commit. This local browser fixture uses actual UPnP/Radix/CSS
  with mock APIs, separate from independent full production UE/UI acceptance.
- Read-only `git apply --check` verifies the candidate patch. Shared source
  fingerprints still match the preflight baseline. Candidate hashes, patch,
  scripts and screenshot/JSON integrity are in `ready.json` and `sha256.json`.
- Independent evidence reviewed:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/pending-results.json`
  and `pending-run.log` in the same directory.

## Next steps

Access owner: review the private three-path patch and grant/apply the exact
writeback/commit window; the UPnP owner will not apply it to the shared checkout
or stage/commit independently. Run affected web tests/final gates and let the
coordinator arrange independent pending-navigation production UE/UI replay.
Existing UE/UI reports remain owned by the independent reviewer. No API,
backend, design or external-resource work is required for this fix.
