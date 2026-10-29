# PandaHome Task Backlog

## Automatic external TCP probe: 2026-10-29

Owners: backend (explicit SSH observer and guarded process lifecycle), UE/UI
(independent code/browser review), integration (deployment, exclusive commits and
evidence). PM coordinates and reviews. Existing DNS, cloud frps, management UI and
service intent are retained; only necessary backend source/configuration change.
Current state: feature `f4ff4f5` passed official-native full gates
(457 API/0 skips, 121 web) and real automatic TCP acceptance. Two new natural
healthy cycles, probe-only trust-failure false, exact-byte restoration/two new
healthy cycles and independent real UI three-state readback passed. API/native
identities stayed fixed during failure/recovery; HTTP continuity was a separate
control. Final 15-predicate audit and independent UI release passed; both
watchdogs/owned Chrome/observer are closed, and final fresh GET remains verified.
Private probe configuration/trust and original product resources are retained.

- [x] Add explicit SSH provider with exact target allowlist, strict host-key and remote-host identity, nonce/fresh UTC/global DNS/actual peer validation and bounded cleanup; preserve HTTPS defaults.
- [x] Independently review guard cleanup and cold-start cancellation fixture; preserve the original failed test and its test-only correction.
- [x] Pass final official-native backend/full hooks: 457 API/0 skips, 121 web, Ruff/ESLint and all hooks passed; commit the reviewed source with normal hooks.
- [x] Deploy API-only from the exact feature commit with owned rollback; preserve web/DB/profile/DNS/cloud frps and existing authorization keys.
- [x] Prove two fresh natural healthy cycles, controlled probe-trust failure removing verification while business/native stay healthy, then automatic restoration and real UI readback. No manual check/detect; TCP scope only.
- [x] Close temporary watchdog/browser resources, retain private probe configuration/trust, and independently audit final sources, stable resources and clean delivery. Final audit: 15/15, 290 source fingerprints, unchanged original DNS/cloud/web; fresh ordinary GET at06:31:53 UTC remains healthy/verified. Final documentation uses normal hooks.

## Relay integration and retained-service takeover: 2026-10-29

Owners: backend (relay profile, TLS trust and guarded SSH/frpc lifecycle),
UE/UI (administrator setup and production-browser acceptance), integration
(deployment, evidence, documentation and exclusive staging/commits).
PM coordinates and independently reviews; PM does not implement or commit.
Current state: feature `950d441` and managed takeover acceptance passed. The retained
`gpufree-code.lets-gpt.com:8081` entry now uses PandaHome-owned guarded SSH/frpc;
both old standalone jobs are stopped and disabled. Real UI EN/ZH × 390/1440,
strict home nonce proofs and final read-only resource checks passed. The original
audit's macOS output-format false is preserved; its fixed-input local 16-check
interpretation passed. Original DNS and cloud frps are retained. Evidence:
`agent_chats/20261029-043527-managed-relay-integration.md`.
This work does not close native P2P direct traversal, company-router ingress,
or the historical unexplained UDP 32783 mapping discrepancy.

- [x] Persist administrator-managed relay settings with redacted token responses, environment defaults, TLS CA/server-name verification and optional SSH transport.
- [x] Verify correct native TLS registration and rejection of wrong CA/server name without fallback; disabled services must start neither SSH nor frpc.
- [x] Pass relevant backend/frontend tests, lint, type checking, production build and normal hooks; independently review and atomically commit the feature before deployment. Official native all-files gates: 428 API/0 skips, 121 web; lint/type/default Turbopack build passed.
- [x] Prepare a frozen source deployment with a fresh private database/state, one API worker and loopback-only API/web; preserve unknown existing databases.
- [x] Through the real UI, save the relay profile and disabled service; prove API/database persistence without claiming live ownership.
- [x] After reviewed cutover, disable and stop both precisely owned standalone launchd jobs; prove PandaHome owns the SSH and frpc children while cloud frps identity stays unchanged.
- [x] From home 1.81, verify normal DNS/FQDN homepage, version, login and anonymous-user authorization; verify disable-negative then enable-positive behavior.
- [x] Restart the API against the same database/profile; verify old-child cleanup, new-child ownership, restored business access and unchanged exact DNS identity/stable fields with zero DNS writes. One actual SIGKILL/recovery and subsequent home nonce proof passed; provider full record/ID/timestamps, original same-value path and zero mutation logs jointly support DNS no-write acceptance.
- [x] Retain a reviewed rollback that stops product-owned children before restoring old SSH/frpc, with no dual KeepAlive owner; record final evidence and retained resources. First-attempt strict observer failure/rollback is preserved. Both cutover watchdogs and the isolated browser/auth profile are closed; managed App/SSH/frpc/DNS/cloud frps remain intentionally active.

## Field Acceptance: field-20261028-183427Z

Owners: Access (public application chain, resource ledger and final shared delivery),
UPnP (physical-router ingress), P2P (direct traversal between separate networks).
PM coordinates and independently reviews; owners implement and submit their work.
Current state: this original run passed committed-source direct application and
physical TCP/UDP transport; its cloud-loopback relay diagnostics did not pass
public ingress. The separate 2026-10-29 retained-service takeover on `950d441`
subsequently satisfied the public relay business requirement with independent
home FQDN/nonce, UI stop/start and API crash-recovery proofs; see the section above.
The original run's resources were removed. The later managed deployment and
retained DNS/cloud frps are intentional long-lived resources. Native P2P direct
and original-39 baseline drift remain unresolved; company physical-WAN ingress
is not proved by the later cloud relay.
Record: `docs/field-acceptance-20261028.md`.

- [x] Direct route: real API + original DnsSync + unique DNS + independent ECS nonce, actual application source/time, same-row port change, revoke and exact cleanup on fe17a0f (4/4 external proofs).
- [x] Public relay business requirement subsequently passed on `950d441` in the separate 2026-10-29 retained-service takeover: real API/UI/native frpc+guarded SSH, home normal FQDN/nonce, stop/start and API crash recovery. The original run's public-control/cloud-loopback diagnostics remain historical non-passes and are not reclassified.
- [x] Physical TCP/UDP transport: real committed API, native 42-character ownership and TCP nonce/change/revoke; final TCP/UDP each 3/3 and own cleanup. Access window original 39 stable fields match; late UDP/final windows start/end at 38.
- [ ] Investigate the later initial-baseline discrepancy: original UDP 32783 is missing before the UDP window, cause unproven; strict original-39 audit fails. Do not restore/adopt/delete an unknown rule.
- [ ] Prove direct P2P traversal between genuinely separate networks, distinguish fallback relay, and independently verify resource cleanup.

## Feature 08: Private P2P TCP Access

Owner: PandaHome maintainers / Codex. Design and operations: `docs/p2p.md`.

- [x] Implement persisted XTCP service intent, encrypted STCP fallback, isolated frpc lifecycle and periodic recovery.
- [x] Add active-admin CRUD, key rotation, protected visitor/CA downloads and a localized `/p2p` management page.
- [x] Verify API authorization, provider recovery, native frp configuration/data transfer, migrations and frontend production build.
- [x] Reuse stable-identity guard/watchdog supervision and verify individual monitor death plus forced-stop cleanup without orphan listeners.
- [x] Restore P2P cancellation focus and verify visible failed-save feedback with retained drafts and retries in EN/ZH desktop/mobile browsers.
- [ ] Validate real direct traversal between separate networks using the deployment's frps/STUN configuration; local validation cannot close this item.

## Feature 07: Managed Public Services

Owner: PandaHome maintainers / Codex. Design: `docs/public-access.md`.

- [x] Step 1 — Record the dual-route design, evidence boundaries, delivery sequence and acceptance criteria.
- [x] Step 2 — Detect public IPv4, upstream NAT, CGNAT and unknown safely, with mocked network tests.
- [x] Step 3 — Integrate native frpc configuration, private credential files and supervised lifecycle, with tests.
- [x] Step 4 — Persist service intent and reconcile DDNS, owned mappings, relay selection, retries, probes and alerts; cover recovery and API authorization.
- [x] Step 5 — Deliver localized guided configuration, actionable network/status feedback and responsive service management; validate tests, lint and production build.
- [x] Step 6 — Complete setup/operations documentation, migration verification, full hooks and final delivery review. Live deployment requires the operator's network and relay configuration.
- [x] Architecture acceptance — Reuse the P2P process guard; prove backend SIGKILL cleanup and same-state/same-port restart, and rerun native frp recovery against the actual client child.
- [x] DDNS update P1 — Pass the original RR to the official SDK; verify all required update fields and real unique-record create, no-write idempotence, same-ID changed value, public/authoritative readback and owned cleanup.
- [x] Access interaction acceptance — Independently verify committed rapid Escape/Cancel/X navigation and full correction after save failures in EN/ZH desktop/mobile browsers.
- [x] Direct field acceptance — Real external application content, DNS, API-managed publish/change/revoke and exact cleanup passed on fe17a0f; see docs/field-acceptance-20261028.md.
- [x] Public relay field acceptance — Subsequently satisfied on `950d441` by the retained managed deployment: real home normal-FQDN/nonce application access, UI pause/re-enable and same-DB API crash recovery. The existing cloud frps/DNS are retained infrastructure; both local transports belong to PandaHome. Earlier cloud-loopback diagnostics remain historical non-passes, and this does not prove company physical-WAN ingress or native P2P direct traversal.

## Feature 01: Core Platform & Tooling Baseline
- [x] Step 1 (Backend) — Audit actual runtime imports (UPnP, auth, Aliyun) and list missing dependencies with required versions.
- [x] Step 2 (Backend) — Declare audited runtime/test dependencies and verify fresh virtualenv `api[test]` installation, configuration, password verification and the backend suite; document the validated host-specific SDK override.
- [x] Step 3 (Backend) — Normalize configuration defaults (`SECRET_KEY`, database URL, Aliyun env names) through `settings` and ensure `.env` loading is consistent.
- [x] Step 4 (Frontend) — Add `src/lib/utils/cn.ts` (class name helper) and `src/lib/api-client.ts` (typed fetch wrapper honoring `NEXT_PUBLIC_API_BASE_URL`).
- [x] Step 5 (Frontend) — Refactor existing fetch calls (status, UPnP, domains) to use the API client and provide uniform empty/error/loading states.
- [x] Step 6 (Shared) — Refresh `.env.example`, `.env.local` template, `README.md`, and `README.zh.md` with unified env variables, install commands, and toolchain notes.

## Feature 02: Authentication & User Management Flow
- [x] Step 1 (Backend) — Introduce dedicated auth settings (token expiry, hashing config) and dependency-injected helpers for FastAPI routes.
- [x] Step 2 (Backend) — Implement `/api/auth/token` (password grant) and repair `/api/users/*` endpoints to enforce RBAC via injected current-user dependency.
- [x] Step 3 (Backend) — Create initial Alembic migration for `users`, add admin bootstrap script/CLI, and document how to seed first admin.
- [x] Step 4 (Backend QA) — Cover token issuance + user CRUD with pytest + FastAPI TestClient (success, invalid credentials, permission denied).
- [x] Step 5 (Frontend) — Build login page (form validation, error feedback), persist token (secure storage), and expose logout handling.
- [x] Step 6 (Frontend) — Protect management routes (domains, UPnP) behind auth, inject token into API client headers, and handle 401 → redirect to login.
- [x] Step 7 (Shared) — Document authentication lifecycle (env requirements, CLI bootstrap, login flow) in READMEs and architecture notes.

## Feature 03: UPnP Port Management Experience
- [x] Step 1 (Backend) — Refactor `UPNPService` into a FastAPI dependency with explicit startup/shutdown, awaited async operations, and clear error enums.
- [x] Step 2 (Backend) — Implement validation helpers (port availability, duplicate mapping detection) and refresh caches after mutations.
- [x] Step 3 (Backend QA) — Add pytest suites mocking UPnP devices to cover status, list, add, delete, and failure scenarios.
- [x] Step 4 (Frontend) — Build mapping CRUD UI: modal form, edit/delete actions, optimistic updates, and toast feedback via API client.
- [x] Step 5 (Frontend) — Ensure list view shows loading skeletons, empty states, and localized error banners for fetch failures.
- [x] Step 6 (Shared) — Write UPnP operations guide (router prerequisites, troubleshooting) under `docs/upnp.md` and reference it from READMEs/agent logs.
- [x] UI follow-up — Fix rapid Escape/Cancel then Tab and delayed outer-menu focus after pending requests; independently pass EN/ZH × 390/1440 rapid-close, success/failure navigation, inline-error retry and second-gateway checks on frozen production source.

## Feature 04: Domain Management Workflow
- [x] Step 1 (Backend) — Define Pydantic schemas for domain + record requests/responses and enforce body payloads instead of query params.
- [x] Step 2 (Backend) — Update routers/service layer to use the schemas, add structured logging, and map Aliyun errors to friendly API messages.
- [x] Step 3 (Backend QA) — Mock Aliyun SDK in pytest to cover list/create/update/delete flows plus error propagation.
- [x] Step 4 (Frontend) — Implement domain/record management UI (create/edit/delete dialogs, inline validation) using the shared API client.
- [x] Step 5 (Frontend) — Expand EN/ZH locale files with all labels used in the domain workflow and ensure navigation text matches.
- [x] Step 6 (Shared) — Document Aliyun setup requirements (API keys, permissions, rate limits) in `docs/domains.md` and link from README + agent logs.

## Feature 05: System Status & Monitoring Dashboard
- [x] Step 1 (Backend) — Design the `/api/status` response contract (cpu, memory, disk, services, timestamps) and extend `/health` with minimal summary data.
- [x] Step 2 (Backend) — Implement metrics gathering (psutil or similar), cache responses, and expose service state derived from real processes or placeholders.
- [x] Step 3 (Backend QA) — Add pytest coverage with patched system metrics to verify successful responses and error handling.
- [x] Step 4 (Frontend) — Build dashboard widgets consuming `/api/status`, including charts/badges, refresh interval controls, and graceful degradation.
- [x] Step 5 (Frontend) — Add missing locale strings (`common.status`, `server.cpuUsage`, etc.) and ensure copy renders correctly in both languages.
- [x] Step 6 (Shared) — Produce monitoring documentation (data sources, update cadence, troubleshooting) and link it in READMEs + ops notes.

## Feature 06: Quality Automation & Process
- [x] Step 1 (Backend) — Scaffold pytest config (`tests/` layout, fixtures, sample test) and register command in `pyproject.toml`.
- [x] Step 2 (Frontend) — Install and configure testing stack (React Testing Library, Vitest or Jest, optional Playwright) with starter specs.
- [x] Step 3 (Shared) — Update pre-commit hooks/CI scripts to run both backend and frontend test suites; document expected commands in README + agent logs.
- [x] Step 4 (Shared) — Maintain `agent_chats/` logbook discipline, including references to docs/tests per feature, and outline follow-up tracking process.
