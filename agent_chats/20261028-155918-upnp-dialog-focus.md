## Summary

Fix two independent UE/UI P2 findings in UPnP dialogs. Add Mapping opened by
Enter then closed with Escape left focus on BODY; the next Tab focused Home and
scrolled the mobile page from 334 to 0. A failed submission's only feedback was a
toast obscured by the still-open modal. Cover Edit and Delete as well, retain
failed drafts, and allow retry. The coordinator explicitly prohibits staging or
committing until a later submission window; preserve the shared index. The
coordinator subsequently granted the next exact-path submission window after
the final focused checks and frontend freeze.

## Changes

- `web/src/components/upnp/mapping-list.tsx`: remember each actual Add, empty-list
  Add, Edit or Delete trigger; restore focus with `preventScroll`, with a stable
  Add-button fallback when the original entry was removed. Defer restoration
  while a successful operation temporarily disables its return target; avoid
  restoring focus when the owning page has unmounted. Memoize edit initial values
  so submission-state rerenders do not reset the draft. Update the list after a
  confirmed write so failure keeps the original opener mounted. Propagate write
  failures to the dialog after existing toast feedback.
- `web/src/components/upnp/mapping-form-dialog.tsx`: forward `onCloseAutoFocus`
  so state-controlled dialogs can restore focus without a DialogTrigger. Catch
  submission errors inside the dialog, retain field values, and clear stale
  validation markers with an explicit `setErrors({})` before a valid submission.
- `web/src/components/upnp/mapping-delete-dialog.tsx`: apply the same close-focus
  contract to deletion confirmation; show local failure feedback and permit retry
  or cancellation. Reset feedback when a new confirmation opens.
- `web/src/components/upnp/dialog-error.tsx`: shared UPnP-local `role="alert"`
  feedback using the existing translated Failed label and API error reason.
  Reveal and focus each failure within the scrollable modal, including repeated
  identical errors, without scrolling the page.
- `web/src/components/upnp/mapping-list.test.tsx`: regression tests use the real
  Radix components, keyboard activation and mocked HTTP, including continuing Tab
  from the opener rather than returning to Home, add/edit draft preservation,
  visible submission errors, retry payloads and delete cancellation after failure.
- `agent_chats/20261028-155918-upnp-dialog-focus.md`: combined implementation,
  focused validation, evidence and handoff record for these two findings.

## Outcome

Fixed and ready for independent UE/UI re-capture. Add dialogs return to the actual
Add Mapping/empty-list Add opener; edit/delete dialogs return to their still-open
Edit/Delete menu item. Escape, Cancel and the form close button share the same
close-focus contract. A removed opener falls back to the stable Add Mapping
button, and temporarily disabled openers regain focus once the write completes.

Add/edit/delete failures appear inside the active modal. Failed drafts remain
editable; repeat submissions can succeed without re-entering values. Repeated
identical errors are revealed again. Reopening a confirmation clears its previous
error. No new translation keys or shared toast-layer changes are needed.

UPnP frontend frozen at 2026-10-28 16:16:52 UTC after the final focused checks.
This delivery stages only the six paths listed above for one atomic commit in
the coordinator's granted window. Shared components, API request semantics and
other sessions' changes are preserved. No real router request, deployment or
push occurred. The isolated fixture server was stopped after verification.

## Verification

- Before the fix, all four initial focus regression tests failed (focus fell on
  BODY); after the fix those four passed.
- Before the submission-feedback change, all three new error/draft/retry
  regressions failed; after the change they passed.
- `npm run test --prefix web -- src/components/upnp/mapping-list.test.tsx src/components/upnp/gateway-manager.test.tsx`:
  **18 passed** (9 focus regressions, 3 submission regressions and 6 existing
  gateway UI tests).
  New tests cover Escape/Cancel/Close followed by Tab, the empty-list Add opener,
  Edit/Delete cancellation and Escape, `preventScroll`, and closing while an
  in-flight write still disables its opener. Submission tests cover a 503 after
  correcting client validation, complete add draft/payload preservation, edit
  draft preservation through rerenders, and failed delete -> Cancel -> reopen ->
  successful retry. All HTTP calls are mocked.
  The invalid -> corrected -> server-503 case asserts that required and both
  invalidPort messages initially appear, then all invalid markers and both old
  message types disappear while the actual server error remains visible.
- `npx --prefix web tsc --noEmit --project web/tsconfig.json --incremental false`:
  passed.
- `npm run lint --prefix web`: passed.
- `git diff --check`: passed.
- Final focused rerun at frontend freeze: 18 passed, TypeScript and ESLint passed.
- `pre-commit run --files web/src/components/upnp/mapping-list.tsx web/src/components/upnp/mapping-form-dialog.tsx web/src/components/upnp/mapping-delete-dialog.tsx web/src/components/upnp/dialog-error.tsx web/src/components/upnp/mapping-list.test.tsx agent_chats/20261028-155918-upnp-dialog-focus.md`:
  passed, including formatting, Web lint and the complete Web test suite. No
  hooks bypassed. The installed pre-commit hook also runs during the final commit.
- The first commit attempt was blocked by two unrelated untracked
  `language-provider.test.tsx` cases: pre-commit hides the unstaged provider
  implementation while leaving its untracked tests visible. The UPnP tests
  passed in that run. All unstaged changes were restored. To preserve the frozen
  shared worktree, the final commit runs the installed hooks from a temporary
  checkout of the exact index via `git checkout-index --all --prefix`, using
  the existing repository/index and a temporary `GIT_WORK_TREE`. This validates
  the actual commit contents without importing or moving other sessions' WIP.
  Dependencies are linked from the existing installation. No hook is skipped.
- Native Chrome keyboard checks in an isolated profile with actual UPnP React
  components and mock API responses passed in EN/ZH at 390px and 1440px. At
  390px, Add Mapping -> Enter -> Escape restores the Add button at scrollY=334;
  the next Tab focuses the row's actions button and scrollY remains 334. Edit
  Escape returns to Edit; Delete Cancel returns to Delete, each without changing
  its preceding scroll position (525 in EN, 505 in ZH). At 1440px, corresponding
  operations retain scrollY=29. No browser runtime exceptions; focus-only checks
  issue no mapping writes.
- Native Chrome error/retry checks in EN/ZH at 390x844 passed with actual UPnP
  components and a separate in-memory mock API. Add, edit and delete 503 reasons
  are fully visible, focused and unobscured inside the modal (`elementFromPoint`
  confirms visibility). Add retains scrollY=334, description, IP and both ports;
  retry POST bodies are identical. A valid submission clears prior validation
  markers. Edit retains the revised description/internal port after a create
  failure and succeeds on retry. Repeated delete 503 is revealed again; Cancel
  returns to Delete at unchanged scrollY=474 (EN) / 454 (ZH), and a reopened
  confirmation retries successfully without stale feedback. No browser runtime
  exceptions. Every read/write uses fake API state; no actual router is contacted.
- Mock-browser evidence and reproducible fixture sources:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-focus-restoration/`.
  `focus-evidence.json` records all four locale/viewport scenarios; PNGs show
  focus after Escape/Tab and after Delete cancellation. `index.html`,
  `preview.tsx`, `server.mjs` and `focus-review.cjs` retain the isolated fixture.
  These are local component-level browser checks, separate from the independent
  full-application review.
- Error evidence and the final fixture sources:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-submit-errors/`.
  `submit-error-evidence.json` records visibility, focus, draft, scroll and request
  assertions. Six 390x844 viewport PNGs show add/edit/delete failures in EN/ZH.
  To reproduce locally, link `node_modules` to this checkout's `web/node_modules`
  in a temporary copy of this fixture, start `node server.mjs`, then run
  `node error-review.cjs` with port 3139 available. Stop that fixture afterward.
- Original independent review evidence:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/interactions.json`.
  Submission-failure screenshot: the same review directory's
  `46-upnp-save-failure-mobile.png`.

## Next steps

Coordinator: run the coordinated production build and independent UE/UI final
re-capture on the frozen integrated frontend. Remaining acceptance is that
integrated build/re-capture; the evidence here proves local component behavior
with mock APIs. No further UPnP frontend edits are planned pending review. Real
router mutation and deployment were not requested or performed. Existing edit
delete/create/rollback API semantics are unchanged.
