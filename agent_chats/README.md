# agent_chats Logbook

All AI or pair-programming sessions that change code must produce a Markdown entry here.

## Naming convention
- `YYYYMMDD-HHMMSS-topic.md`, use 24h UTC timestamps.
- Use lowercase kebab-case topic summaries.

## Required sections
Each log must include the following headings:

- `## Summary` — short description of the request and context
- `## Changes` — bullet list of touched files / highlights
- `## Outcome` — results, current status, unresolved points
- `## Verification` — commands run, expected vs actual results (state "Not run" when skipped)
- `## Next steps` — follow-ups, TODOs, blockers

## Authoring tips
- Reference files with project-relative paths (e.g. `api/src/app/main.py`).
- Prefer ASCII; document any non-ASCII usage.
- Keep entries committed alongside the code they describe.
