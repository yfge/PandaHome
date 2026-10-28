# Concurrent delivery integration review

## Summary

Record the project manager's independent review of three existing PandaHome
chats and the public-access owner's final delivery of all remaining shared files.
The user's final instruction assigns coding and commits to the Access owner;
the project manager retains coordination and independent acceptance only.

## Changes

- `docs/integration-review.md`: ownership, acceptance gates and evidence limits.
- `web/src/app/domains/[domain]/records/page.tsx`: consume promised route params
  with React `use`, matching the installed Next.js 16 page contract.
- `api/src/app/main.py`, `api/tests/test_lifespan.py`: register cleanup before
  startup and unwind every owner even if initialization or another cleanup fails.
- `api/tests/test_transport_isolation.py`: exercise public relay and private P2P
  together under one state root, including independent credentials and shutdown.
- `web/src/components/providers/language-provider.tsx` and
  `web/src/components/providers/language-provider.test.tsx`: synchronize the
  document's language with English/Chinese UI, including persisted reopening.
- `AGENTS.md`, `README.md`, `README.zh.md`: align the stated framework version
  with the installed Next.js 16 toolchain. `CLAUDE.md` is a regular pointer
  document; correct its handbook filename case to `AGENTS.md`.
- `api/.env.example`, `api/pyproject.toml`, `docs/auth-lifecycle.md` and
  `docs/backend-dependency-audit.md`: reproducible fresh setup, valid hashing
  array, declared email/test dependencies, compatible bcrypt backend, explicit
  SQLite cwd and host-specific native build evidence. Dedicated atomic logs
  accompany the manifest and two test-portability fixes.
- `docs/ue-ui-review.md` and `agent_chats/20261028-160200-ue-ui-review.md`:
  independent report and appended committed-Access recheck, retaining original
  screenshots and evidence precedence. Product fixes remain separate commits.
- `tasks.md`: shared UI delivery and explicit real-DNS/DDNS evidence boundaries.
- `agent_chats/20261028-163933-real-dns-acceptance.md`: unchanged gateway-owner
  real cloud lifecycle evidence, included in the final documentation delivery.

## Outcome

Initial API session failures and the Next.js params blocker are fixed. Access
rapid-close focus and stale-error typing are independently accepted at `e3775d1`.
Public relay and P2P share the same guard and have backend-death recovery proof.
The DDNS missing-RR P1 is closed by `e2e4b22`, official-SDK-request regressions
and a real same-ID update, with owned cleanup confirmed.

Final product source `4efe286` passes 373 native-enabled backend tests,
103 frontend tests, lint/type, the complete production build and all-files hooks.
The UPnP rapid-close follow-up and newly exposed pending outer-menu close are
fixed by its original owner and atomically delivered by Access in `e8be058` and
`4efe286`.
The independent reviewer has now closed both follow-ups at the frozen hashes:
overall UI sign-off is restored with no open UE/UI blockers. Access delivers all
remaining shared documentation in this final unit. No coding or commit is left
for the project manager.

## Verification

- Initial `pytest -q api/tests`: 239 passed, three access API session failures.
- Initial `npm run test --prefix web`: 26 passed.
- Initial `npm run lint --prefix web`: passed.
- `pytest -q api/tests/test_lifespan.py api/tests/test_transport_isolation.py`:
  five passed; targeted Ruff passed.
- Isolated `npm run build` on all three integrated pages: passed with the default
  Next.js 16.1.6 Turbopack production builder, including TypeScript.
- Existing SQLite user data survived Alembic upgrade from `20251029_01` to head,
  downgrade to `20251029_01`, and upgrade to head again. Fresh migration tests
  also passed. No operator database was used.
- `python api/tests/integration/frp_smoke.py --bin-dir <verified-frp-directory>`:
  real loopback TCP/UDP forwarding, reconnect, crash recovery, native registration
  and unrelated-port rejection passed; owned child and secret file were removed.
- `PANDAHOME_FRP_BIN_DIR=<verified-frp-directory> python -m pytest -q api/tests/test_p2p_native.py`:
  three initial loopback XTCP/STCP/revocation checks passed. The added native
  abrupt-backend-death regression is now included in the final 373 passing tests.
- Full staged snapshot `pre-commit run --all-files`: passed after the hooks
  normalized three P2P EOFs in the snapshot. Final source must include those
  normalizations; the shared source index was never altered for snapshot checks.
- Earlier Access-owner integrated checks on `2ef29ac`, UTC 17:21:09–17:21:55:
  `PANDAHOME_FRP_BIN_DIR=<verified-frp-directory> PYTHONPATH=api python -m pytest -q api/tests`:
  **373 passed, no skips, 44.38 s**. A process-local disposable default SQLite
  URL isolates this run from operator databases.
- Earlier pre-UPnP-follow-up `npm run test --prefix web`: **91 passed / 10 files**;
  `ruff check api`, `npm run lint --prefix web`, `npx tsc --noEmit --incremental false`
  from `web/`, and default `npm run build --prefix web`: passed. Next.js 16.1.6
  Turbopack generated 11 pages; no webpack fallback.
- Independent fresh Python 3.13.5 virtualenv snapshot: **369 passed, 4 optional
  native cases skipped**; editable `api[test]`, pip check, shipped env parsing,
  real password hash/verify, TestClient and read-only netifaces calls passed.
  This host required an existing compatible SDK selected for the pip process
  only. See `20261028-171555-clean-setup-verification.md` for negative cases,
  versions and source hashes; no system toolchain or runtime default changed.
- Real public-relay post-guard smoke and P2P native backend-death/revocation
  results are recorded in `20261028-162733-public-relay-restart-acceptance.md`.
  Smoke identifies and kills native frpc, rather than confusing its PID with
  the guard. Shared backend tests include real same-state/port restart proof.
- Independent committed Access browser acceptance at `e3775d1`: EN/ZH ×
  390/1440, 48 native rapid-close groups, eight complete stale-error correction
  paths and 28 viewed screenshots passed. API responses were mocked.
- User-authorized real DDNS at unique `pan-qa-ddns-20261028165501-cc7ba5`:
  Add/Update/Delete exactly 1/1/1, unchanged record ID, repeated inputs no write,
  changed value confirmed by provider, both authorities and two public
  resolvers. Finally two provider reads and both authoritative NXDOMAIN/AA
  confirmed deletion. Separate gateway CNAME test also cleaned its owned ID.
- Earlier snapshot hook evidence above is preserved as history; the latest
  integrated runs below supersede it.
- Final product-source frontend checks on `e8be058`, UTC 17:31:05–17:31:21:
  **100 passed / 10 files**, ESLint, complete default Turbopack build/11 pages
  and standalone TypeScript passed. The 189-file source hash comparison against
  `2ef29ac` found changes only in the two UPnP source/test files.
- Prior integrated `pre-commit run --all-files --verbose` on `e8be058`, UTC
  17:31:59–17:32:51: **all hooks passed**, including native backend **373 passed,
  no skips, 43.37 s** and frontend **100 passed**. No hooks were bypassed and
  no SKIP setting was used. Raw command logs and fingerprints are retained in
  `final-acceptance-20261028/` under the Access evidence root.
- Final source `4efe286`: complete production build/11 pages and standalone
  TypeScript passed; latest actual `pre-commit run --all-files --verbose`, UTC
  17:50:13–17:51:09: **all hooks passed**, including Ruff/ESLint, native backend
  **373 passed, no skips, 45.37 s**, and frontend **103 passed / 10 files**.
  No hook skip or bypass. Source fingerprints still differ from `2ef29ac` only
  in UPnP mapping-list source/test; API/DDNS source is unchanged.
- Independent final UPnP production review on `4efe286`: 3/3 original failure
  reproductions now pass; **48/48** Add/Edit/Delete × success/503 × continued
  navigation/no-navigation groups pass across EN/ZH × 390/1440. **12/12** inline
  error, draft and successful-retry cases plus **4/4** ordinary-menu Escape
  controls pass; 25 new screenshots were viewed. The earlier rapid-close 48
  results remain accepted. Product hashes match the commit, route HTTP200 and
  default production build pass, and owned preview/Chrome listeners are stopped.
  See the independent report's Final UPnP menu acceptance; no real API writes.

## Next steps

No local implementation or documentation work remains after this final shared
unit; Main PM retains independent review only. Preserve original UE/UI evidence
and both unique DNS lifecycle records. External application ingress, physical router behavior and
separate-network traversal remain unverified deployment acceptance items; no
TEST-NET DNS result or loopback relay test closes them. No push, deployment,
existing DNS mutation, password change or real router write was performed.
