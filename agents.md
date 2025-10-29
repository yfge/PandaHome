# PandaHome Agents Handbook

This document is the single source of truth for all coding agents collaborating on PandaHome. Follow every guideline unless the user explicitly overrides it.

## 1. Mission & Scope

- Deliver a reliable home-server cockpit that manages Aliyun DDNS and UPnP port mappings from a modern Next.js dashboard and a FastAPI backend.
- Keep the codebase auditable: every change should be reproducible from chat logs, tests, and documentation.
- Optimise for maintainability—prefer clarity over cleverness, document decisions, and surface follow-up work.

## 2. Repository Layout & Ownership

- `api/` — FastAPI service (Python 3.12, SQLAlchemy, Aliyun + UPnP integrations).
  - `src/app/routers/` HTTP endpoints per domain (`domains`, `upnp`, ...).
  - `src/app/services/` core orchestration (Aliyun DNS client, UPnP controller).
  - `src/app/models/` SQLAlchemy models and Pydantic schemas.
  - `pyproject.toml` drives packaging + Ruff configuration.
- `web/` — Next.js 15 app router (TypeScript, Tailwind 4, shadcn/ui).
  - `src/app/` routing + layouts, `src/components/` UI primitives, `src/config/` constants, `src/i18n/` translations.
  - `package.json` uses npm scripts (`npm run dev|build|start|lint`).
- `agent_chats/` — required logbook for AI collaborations (see §5).
- `scripts/` — helper scripts invoked by hooks (`ensure_agent_chat.sh`, `run_web_lint.sh`).

Keep this structure tidy; prefer adding new domains under the existing patterns.

## 3. Toolchain Expectations

- Python: 3.12+. Use `uv` or `pip` with virtualenv; install deps via `pip install -e api` or `uv pip install -e api` (document exact command in logs).
- Node.js: LTS 20.x or 22.x with npm. Install web deps via `npm install` inside `web/`.
- Docker usage should be documented before introducing new containers.
- Infrastructure secrets (`ALIYUN_*`, etc.) live in `.env` files that are never committed; provide `.env.example` updates when new variables are required.

## 4. Quality Gates & Hooks

- `pre-commit` is mandatory. Install locally:
  ```bash
  pip install pre-commit  # or uv tool install pre-commit
  pre-commit install --install-hooks
  ```
- Hook pipeline definition lives in `.pre-commit-config.yaml`:
  - `pre-commit-hooks` bundle: whitespace, EOF, YAML/JSON validation.
  - `ruff`: lint/fix Python inside `api/`.
  - `scripts/ensure_agent_chat.sh`: blocks commits that touch code without an `agent_chats` entry; validates naming + sections.
  - `scripts/run_web_lint.sh`: runs `npm run lint` when `web/node_modules` exists.
- Keep hooks fast (<1 min). When they fail, fix the root cause; do not bypass except for emergencies (document any skip in `agent_chats`).
- Run `pre-commit run --all-files` before opening pull requests.

## 5. `agent_chats/` Process

- Every code-producing session must add a log entry. Template headings (exact case):
  1. `## Summary`
  2. `## Changes`
  3. `## Outcome`
  4. `## Verification`
  5. `## Next steps`
- File naming: `YYYYMMDD-HHMMSS-topic.md` using UTC. Use lowercase kebab-case topic labels.
- Reference touched files (`api/src/...`, `web/src/...`) and include snippets when helpful.
- Document the concrete work performed, list the files changed, and call out any blockers or decisions with brief reasoning.
- Capture test commands, even if skipped (write `Not run – reason`).
- Store risks, blockers, TODOs under `## Next steps` for traceability.

## 6. Coding Conventions

### Backend (FastAPI)
- Prefer dependency-injected services rather than module-level singletons.
- Use Pydantic models for request/response validation; keep them in `schemas/`.
- Wrap Aliyun + UPnP clients behind service interfaces; surface typed errors.
- Database migrations should be created via Alembic (document command in logs).
- Enforce `ruff` style; avoid unused imports, keep functions < 50 lines when reasonable.

### Frontend (Next.js)
- Co-locate UI state with components; avoid global mutable state.
- Use `@/` absolute imports; update `tsconfig.json` when new paths are introduced.
- Follow shadcn/ui style guidelines; rely on Tailwind tokens instead of raw hex colours.
- Keep i18n keys in English; update locale files when adding strings.
- Ensure all async effects handle errors and display user feedback.

## 7. Commit & Review Policy

- Keep every commit atomic—limit changes to the smallest coherent unit of work and avoid bundling unrelated edits.
- Use Conventional Commits (`type(scope?): message`). Common types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`.
- Never squash away `agent_chats` history; each commit should link to a log entry.
- When raising PRs, summarise the corresponding chat log(s) and verification steps.
- For reviews, focus on correctness, observability, and deployability before polish.

## 8. Documentation Requirements

- Update `README.md` / `README.zh.md` whenever setup steps change.
- Document new modules or workflows in `/docs` (create if needed) and reference them from `agent_chats`.
- Keep this `agents.md` current; if instructions change, update here first and sync other agent files (e.g., `CLAUDE.md`).

## 9. Incident & Risk Handling

- If hooks must be skipped, note the exact command and reason inside the relevant `agent_chats` entry and open a follow-up task.
- For production-impacting bugs, add a `## Incident` section to the log with timeline and mitigation.
- Capture technical debt items under `## Next steps` with owners or due dates when possible.

## 10. Useful Commands

- Backend lint/format: `uv run ruff check api && uv run ruff format api`
- Backend dev server: `uvicorn src.app.main:app --reload --app-dir api/src`
- Frontend dev server: `npm run dev --prefix web`
- Run hooks on demand: `pre-commit run --all-files`

Stay disciplined: small, well-documented commits + enforced hooks keep PandaHome healthy.

## 11. Environment & API Reference

- Backend `.env` expects:
  - `ALIYUN_ACCESS_KEY_ID`
  - `ALIYUN_ACCESS_KEY_SECRET`
  - `ALIYUN_REGION_ID`
- Frontend `.env.local` expects:
  - `NEXT_PUBLIC_API_BASE_URL`
- Key API routes exposed by FastAPI:
  - `GET /api/upnp/mappings`, `POST /api/upnp/mappings`, `DELETE /api/upnp/mappings/{id}`
  - `GET /api/domains/domains`, `POST /api/domains/domains`
  - `GET /api/domains/domains/{domain}/records`, `POST`, `PUT`, `DELETE /api/domains/domains/{domain}/records/{record_id}`
- When expanding the API, update router docs (`api/src/app/routers/*`) and sync README files in both English and Chinese.
