#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
source scripts/runtime.sh
.venv/bin/python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT
cd apps/web
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
