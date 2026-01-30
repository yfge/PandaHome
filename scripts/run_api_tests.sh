#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d "api" ]]; then
  exit 0
fi

if ! command -v python >/dev/null 2>&1; then
  echo "[api tests] python not found on PATH." >&2
  exit 1
fi

if ! command -v pytest >/dev/null 2>&1; then
  echo "[api tests] pytest not found on PATH (install with: pip install -e api[test])." >&2
  exit 1
fi

if ! python -c "import src.app" >/dev/null 2>&1; then
  echo "[api tests] Backend package not importable. Run: pip install -e api[test]" >&2
  exit 1
fi

pytest -q api/tests
