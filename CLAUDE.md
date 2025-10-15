# CLAUDE.md

`agents.md` is the canonical handbook for every coding agent in this repository. Always read and follow it first.

Quick reminders for Claude Code:

- Log every code-producing session in `agent_chats/` using the required template before committing.
- Run `pre-commit install --install-hooks` and keep hooks green (Ruff + Next.js lint).
- Keep back-end changes under `api/`, front-end under `web/`, and document updates in both `README.md` and `README.zh.md` when setup steps change.
- Record verification commands and follow-ups in the paired `agent_chats` entry so humans can audit the change.

If guidance seems missing or inconsistent, update `agents.md` first, then sync any auxiliary agent files.
