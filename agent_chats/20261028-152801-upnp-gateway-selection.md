## Summary

Deliver explicit UPnP gateway selection for nested routers, preserving the
parallel Access/P2P services and their default-gateway/ownership contracts.
Acceptance coordination: chat 01a18323-4d6f-7cb1-819a-cf6e1cab4dab. Authorized
scope includes one atomic local commit; no real-router writes, deployment or push.

## Changes

Final changed paths (20 files; README edits contain only the UPnP feature bullet):

- `README.md`
- `README.zh.md`
- `docs/upnp.md`
- `docs/upnp-multiple-routers.md`
- `api/src/app/routers/upnp.py`
- `api/src/app/routers/upnp_gateway.py`
- `api/src/app/schemas/upnp_gateway.py`
- `api/src/app/services/upnp_gateway.py`
- `api/tests/test_upnp_gateway.py`
- `web/src/app/upnp/page-client.tsx`
- `web/src/components/upnp/mapping-list.tsx`
- `web/src/components/upnp/mapping-form-dialog.tsx`
- `web/src/components/upnp/mapping-delete-dialog.tsx`
- `web/src/components/upnp/gateway-api.ts`
- `web/src/components/upnp/gateway-manager.tsx`
- `web/src/components/upnp/gateway-manager.test.tsx`
- `web/src/components/upnp/gateway-translations.ts`
- `web/src/i18n/locales/upnp-gateways/en.json`
- `web/src/i18n/locales/upnp-gateways/zh.json`
- `agent_chats/20261028-152801-upnp-gateway-selection.md`

Backend: independently discover/inspect IGDs, or use a known upstream description
URL even if default discovery failed. Request-scoped targets support
WANIPConnection v1/v2 and WANPPPConnection v1; typed validation rejects unsafe URL
syntax, missing IPv4 targets, disabled creates and out-of-range leases. New routes
require an active administrator. Existing default UPnP routes remain compatible.

Creation checks the exact port/protocol and refuses to overwrite an existing
rule. Deletion explicitly addresses only the selected router and port/protocol;
this is manual administrator control, not Access background ownership or cleanup.
Unsupported enumeration is distinguished from an empty table and is not needed
for add/delete. Transport failures are not reported as successful empty lists.

Frontend: choose discovered devices or inspect a manual URL; show WAN address
scope without claiming external reachability. Every CRUD request encodes its
selected device URL. Router changes reset drafts, and editing/writes lock target
selection. Responsive cards, loading skeletons and long names fit small screens;
forms scroll within a reduced viewport. Action buttons have localized accessible
names, and delete confirmation uses valid paragraph markup. Dedicated EN/ZH
locale files avoid concurrent shared translation edits.

## Outcome

Delivered as one atomic local feature with Conventional Commit subject
`feat(upnp): manage explicit gateways across NAT layers`. The commit is gated by
the repository's original pre-commit configuration. Only exact owned paths and
the two README UPnP hunks are staged; no `git add .` is used.

Explicit gateway errors never fall back to the default router. Default UPnP
service state, monitoring, Access reconciliation, P2P, startup, config,
navigation, migrations, shared translations and their other WIP remain untouched
by this delivery. Selection is page/request scoped, not a persistent global
setting. Multi-layer NAT requires separate mappings on each participating router.

To preserve concurrent WIP, the commit hook runs the unchanged configured
pre-commit pipeline on an isolated export of the exact staged tree. The hook
checks the source tree/parent before and after validation; it never stashes or
rewrites another session's work. Validation output and the tree receipt are
retained with the browser evidence below. No hook or quality gate is skipped.

## Verification

Environment: Python 3.13.5, Node 20.19.5, existing backend/web dependencies.
No dependency installation was necessary.

- `pytest -q api/tests/test_upnp_gateway.py api/tests/test_upnp.py`: **48 passed**.
  Covers default API compatibility, exact targeting, concurrent clients, failed
  add/delete without fallback, active-admin checks on all new route families,
  collision preservation, TCP/UDP and router isolation, missing action metadata,
  bounded enumeration/discovery, cancellation, session cleanup and HTTP timeout
  against a local stalled HTTP server. No physical IGD is contacted.
- `npm run test --prefix web`: shared-checkout snapshot **40 passed**, including
  **6 gateway UI tests**. Covers target retention after failed inspection,
  draft reset, disabled target switching, unmount handling and URL encoding.
- `npm run lint --prefix web`: passed.
- `npx --prefix web tsc --noEmit --project web/tsconfig.json --incremental false`:
  passed with the shared checkout's generated development types.
- `python -m ruff check api/src/app/schemas/upnp_gateway.py api/src/app/services/upnp_gateway.py api/src/app/routers/upnp_gateway.py api/tests/test_upnp_gateway.py`: passed.
- `git diff --check`: passed.
- Required commit hook: `pre-commit run --verbose --files <the 20 paths above>`
  on the isolated staged-tree export. Exact command output and a passed-tree
  receipt are saved as `commit-pre-commit.log` and `commit-receipt.json` in the
  evidence directory. The same configured whitespace/JSON/Ruff/ledger/web lint/
  API tests/web tests all execute; validation includes the complete tests present
  in the committed tree, rather than unrelated uncommitted source files.
- Shared-tree pre-commit run before export: API tests **347 passed, 4 skipped**;
  other checks passed, but concurrent file writes made pre-commit report
  "files were modified by this hook". This run alone is not a clean gate result;
  the immutable staged-tree run above is the commit gate.
- Previous three Access API failures were fixed by its owning chat:
  `pytest -q api/tests/test_access_api.py`: **16 passed** on recheck.

Browser acceptance uses actual UPnP React components, the repository Tailwind
styles, an isolated Vite fixture and a private headless Chrome profile. All API
responses are simulated, including failures; no router mapping is written.
Both EN/ZH pass at **320px and 390px** widths with no horizontal overflow. At
**390x480**, the mapping form scrolls and its action buttons remain reachable.
The normal 390x844 add dialog stays within x=16..374. Default/selected lists,
failed manual checks, disabled selection during editing, add/delete confirmation
and a 1440px desktop view were exercised. No browser runtime exceptions occurred.
Screenshots were visually inspected.

Evidence directory (absolute local path):
`/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-acceptance/`

- `evidence.json`: browser measurements, assertions and simulated API calls.
- `changed-paths.json`: complete absolute changed-path manifest.
- `upnp-mobile-en.png`, `upnp-mobile-zh.png`: responsive selected-router lists.
- `upnp-mobile-dialog-en.png`, `upnp-mobile-dialog-zh.png`: add dialogs.
- `upnp-mobile-dialog-short-en.png`, `upnp-mobile-dialog-short-zh.png`: reduced-height scrolling.
- `upnp-mobile-delete-en.png`, `upnp-mobile-delete-zh.png`: delete confirmations.
- `upnp-desktop-en.png`: desktop layout.
- `index.html`, `preview.tsx`, `server.mjs`, `review.cjs`: fixture/review source.
  Link `node_modules` to the repository's installed web dependencies, start
  `node server.mjs`, then run `node review.cjs` to reproduce on this Mac.

Earlier isolated `npm run build -- --webpack` compiled JavaScript successfully,
but failed on the pre-existing Next.js 16 synchronous domain-page params contract.
The coordinator owns that fix and final integrated production build verification;
this chat does not overwrite its domain-page or shared integration changes.

## Next steps

- Coordinator: independently verify the settled integrated tree and production
  build after its Next.js 16 route fix. The UPnP domain has no known local blocker.
- Operator acceptance remains separate: obtain reachable upstream description
  URLs, verify access policy, configure each NAT layer and test actual inbound
  reachability from an external network. This task prohibits real-router writes.
- Another client can race between the collision query and SOAP mutation. Manual
  deletes are explicit administrator actions and do not carry persistent Access
  ownership tokens; there is no automatic cross-layer transaction or cleanup.
- After a write timeout, inspect the selected router before retrying: losing the
  response does not prove it left the rule unchanged. An inaccessible ISP CGNAT
  requires operator support or a different access mechanism.
