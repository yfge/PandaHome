#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d "web" ]]; then
  exit 0
fi

if [[ ! -d "web/node_modules" ]]; then
  echo "[web tests] Skipping frontend tests (run npm install inside web/ first)." >&2
  exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[web tests] npm not found on PATH." >&2
  exit 1
fi

cd web
npm run test
