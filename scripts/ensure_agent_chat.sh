#!/usr/bin/env bash
set -euo pipefail

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  BASE_REF=HEAD
else
  BASE_REF=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

CODE_CHANGES=$(git diff --name-only --cached "$BASE_REF" -- \
  'api/**' \
  'web/**' \
  'scripts/**' \
  '*.py' \
  '*.ts' \
  '*.tsx' \
  '*.js' \
  '*.jsx' \
  '*.sh' \
  '*.json' \
  ':!agent_chats/**'
)

AGENT_LOGS=$(git diff --name-only --cached -- 'agent_chats/*.md' || true)

if [[ -n "$CODE_CHANGES" && -z "$AGENT_LOGS" ]]; then
  cat >&2 <<'MSG'
[agent_chats] Commit includes code changes but no updated log.
Add a new entry under agent_chats/ following YYYYMMDD-HHMMSS-topic.md with required sections.
MSG
  exit 1
fi

if [[ -z "$AGENT_LOGS" ]]; then
  exit 0
fi

name_regex='^agent_chats/[0-9]{8}-[0-9]{6}-[a-z0-9-]+\.md$'
missing_sections=0

for file in $AGENT_LOGS; do
  if [[ ! $file =~ $name_regex ]]; then
    echo "[agent_chats] $file does not match required pattern YYYYMMDD-HHMMSS-topic.md" >&2
    exit 1
  fi

  if ! grep -q '^## Summary' "$file"; then
    echo "[agent_chats] $file missing '## Summary' section" >&2
    missing_sections=1
  fi
  if ! grep -q '^## Changes' "$file"; then
    echo "[agent_chats] $file missing '## Changes' section" >&2
    missing_sections=1
  fi
  if ! grep -q '^## Outcome' "$file"; then
    echo "[agent_chats] $file missing '## Outcome' section" >&2
    missing_sections=1
  fi
  if ! grep -q '^## Verification' "$file"; then
    echo "[agent_chats] $file missing '## Verification' section" >&2
    missing_sections=1
  fi
  if ! grep -q '^## Next steps' "$file"; then
    echo "[agent_chats] $file missing '## Next steps' section" >&2
    missing_sections=1
  fi

done

if [[ $missing_sections -eq 1 ]]; then
  exit 1
fi
