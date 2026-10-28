# CLAUDE.md

[AGENTS.md](AGENTS.md) is the canonical handbook for every coding agent in this repository. Always read and follow it first.

Quick reminders for Claude Code:

- Log every code-producing session in `agent_chats/` using the required template before committing.
- Run `pre-commit install --install-hooks` and keep hooks green (Ruff, ESLint and backend/frontend tests).
- The frontend uses Next.js 16; use the commands in `web/package.json`.
- Keep the backend virtual environment active. Because `sqlite:///./app.db` is relative to the current working directory, run `alembic upgrade head`, `bootstrap-admin`, and `uvicorn src.app.main:app --port 8003` from the same `api/` directory. Do not move databases or run migrations automatically.
- Start the frontend in another terminal at the repository root with `npm run dev --prefix web`.
- Keep back-end changes under `api/`, front-end under `web/`, and document updates in both `README.md` and `README.zh.md` when setup steps change.
- Record verification commands and follow-ups in the paired `agent_chats` entry so humans can audit the change.

If guidance seems missing or inconsistent, update `AGENTS.md` first, then sync any auxiliary agent files.
