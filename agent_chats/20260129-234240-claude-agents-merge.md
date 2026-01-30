## Summary

- Merged `CLAUDE.md` guidance into the main agent handbook and made `CLAUDE.md` a symlink entrypoint.
- Normalized handbook filename to `AGENTS.md` and updated README references.

## Changes

- `AGENTS.md`: clarified canonical agent handbook and noted `CLAUDE.md` is a symlink to it.
- `CLAUDE.md`: replaced file content with a symlink to `AGENTS.md`.
- `README.md`: updated handbook reference to `AGENTS.md`.
- `README.zh.md`: updated handbook reference to `AGENTS.md`.

## Outcome

- Repository now has a single source of truth (`AGENTS.md`); `CLAUDE.md` points to it via symlink for tool compatibility.

## Verification

- `ls -la CLAUDE.md && readlink CLAUDE.md`
- `git status --porcelain`
- Not run – no app/test changes required for this doc-only update.

## Next steps

- Run `pre-commit run --all-files` before committing to ensure hooks remain green.
