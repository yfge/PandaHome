# PandaHome Task Backlog

## Feature 01: Core Platform & Tooling Baseline
- [x] Step 1 (Backend) — Audit actual runtime imports (UPnP, auth, Aliyun) and list missing dependencies with required versions.
- [x] Step 2 (Backend) — Update `api/pyproject.toml` to include the audited deps (`async-upnp-client`, `aiohttp`, `netifaces`, `python-jose`, `passlib`, etc.) and verify `uv pip install -e api` succeeds.
- [x] Step 3 (Backend) — Normalize configuration defaults (`SECRET_KEY`, database URL, Aliyun env names) through `settings` and ensure `.env` loading is consistent.
- [x] Step 4 (Frontend) — Add `src/lib/utils/cn.ts` (class name helper) and `src/lib/api-client.ts` (typed fetch wrapper honoring `NEXT_PUBLIC_API_BASE_URL`).
- [x] Step 5 (Frontend) — Refactor existing fetch calls (status, UPnP, domains) to use the API client and provide uniform empty/error/loading states.
- [x] Step 6 (Shared) — Refresh `.env.example`, `.env.local` template, `README.md`, and `README.zh.md` with unified env variables, install commands, and toolchain notes.

## Feature 02: Authentication & User Management Flow
- [x] Step 1 (Backend) — Introduce dedicated auth settings (token expiry, hashing config) and dependency-injected helpers for FastAPI routes.
- [x] Step 2 (Backend) — Implement `/api/auth/token` (password grant) and repair `/api/users/*` endpoints to enforce RBAC via injected current-user dependency.
- [ ] Step 3 (Backend) — Create initial Alembic migration for `users`, add admin bootstrap script/CLI, and document how to seed first admin.
- [ ] Step 4 (Backend QA) — Cover token issuance + user CRUD with pytest + FastAPI TestClient (success, invalid credentials, permission denied).
- [ ] Step 5 (Frontend) — Build login page (form validation, error feedback), persist token (secure storage), and expose logout handling.
- [ ] Step 6 (Frontend) — Protect management routes (domains, UPnP) behind auth, inject token into API client headers, and handle 401 → redirect to login.
- [ ] Step 7 (Shared) — Document authentication lifecycle (env requirements, CLI bootstrap, login flow) in READMEs and architecture notes.

## Feature 03: UPnP Port Management Experience
- [ ] Step 1 (Backend) — Refactor `UPNPService` into a FastAPI dependency with explicit startup/shutdown, awaited async operations, and clear error enums.
- [ ] Step 2 (Backend) — Implement validation helpers (port availability, duplicate mapping detection) and refresh caches after mutations.
- [ ] Step 3 (Backend QA) — Add pytest suites mocking UPnP devices to cover status, list, add, delete, and failure scenarios.
- [ ] Step 4 (Frontend) — Build mapping CRUD UI: modal form, edit/delete actions, optimistic updates, and toast feedback via API client.
- [ ] Step 5 (Frontend) — Ensure list view shows loading skeletons, empty states, and localized error banners for fetch failures.
- [ ] Step 6 (Shared) — Write UPnP operations guide (router prerequisites, troubleshooting) under `docs/upnp.md` and reference it from READMEs/agent logs.

## Feature 04: Domain Management Workflow
- [ ] Step 1 (Backend) — Define Pydantic schemas for domain + record requests/responses and enforce body payloads instead of query params.
- [ ] Step 2 (Backend) — Update routers/service layer to use the schemas, add structured logging, and map Aliyun errors to friendly API messages.
- [ ] Step 3 (Backend QA) — Mock Aliyun SDK in pytest to cover list/create/update/delete flows plus error propagation.
- [ ] Step 4 (Frontend) — Implement domain/record management UI (create/edit/delete dialogs, inline validation) using the shared API client.
- [ ] Step 5 (Frontend) — Expand EN/ZH locale files with all labels used in the domain workflow and ensure navigation text matches.
- [ ] Step 6 (Shared) — Document Aliyun setup requirements (API keys, permissions, rate limits) in `docs/domains.md` and link from README + agent logs.

## Feature 05: System Status & Monitoring Dashboard
- [ ] Step 1 (Backend) — Design the `/api/status` response contract (cpu, memory, disk, services, timestamps) and extend `/health` with minimal summary data.
- [ ] Step 2 (Backend) — Implement metrics gathering (psutil or similar), cache responses, and expose service state derived from real processes or placeholders.
- [ ] Step 3 (Backend QA) — Add pytest coverage with patched system metrics to verify successful responses and error handling.
- [ ] Step 4 (Frontend) — Build dashboard widgets consuming `/api/status`, including charts/badges, refresh interval controls, and graceful degradation.
- [ ] Step 5 (Frontend) — Add missing locale strings (`common.status`, `server.cpuUsage`, etc.) and ensure copy renders correctly in both languages.
- [ ] Step 6 (Shared) — Produce monitoring documentation (data sources, update cadence, troubleshooting) and link it in READMEs + ops notes.

## Feature 06: Quality Automation & Process
- [ ] Step 1 (Backend) — Scaffold pytest config (`tests/` layout, fixtures, sample test) and register command in `pyproject.toml`.
- [ ] Step 2 (Frontend) — Install and configure testing stack (React Testing Library, Vitest or Jest, optional Playwright) with starter specs.
- [ ] Step 3 (Shared) — Update pre-commit hooks/CI scripts to run both backend and frontend test suites; document expected commands in README + agent logs.
- [ ] Step 4 (Shared) — Maintain `agent_chats/` logbook discipline, including references to docs/tests per feature, and outline follow-up tracking process.
