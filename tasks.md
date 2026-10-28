# PandaHome Task Backlog

## Field Acceptance: field-20261028-183427Z

Owners: Access (public application chain, resource ledger and final shared delivery),
UPnP (physical-router ingress), P2P (direct traversal between separate networks).
PM coordinates and independently reviews; owners implement and submit their work.
Current state: live capability preflight in progress; no field check has passed.
Record: `docs/field-acceptance-20261028.md`.

- [ ] Exercise an actual nonce application managed by the real PandaHome API, unique DNS, independent external-client resolution/request, matching backend nonce/time/source, changes and revocation; record direct and relay results separately.
- [ ] Prove ingress through a controlled physical router using only an owned temporary mapping and an independent external request; verify removal and cleanup.
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
- [ ] Deployment acceptance — Verify an actual public application endpoint from outside the home network; DNS cloud/public resolution and loopback frp evidence do not close this item.

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
