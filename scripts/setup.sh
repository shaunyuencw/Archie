#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
source scripts/runtime.sh
if [ ! -x .venv/bin/python ]; then
  archie_python=$(command -v python3.12 || true)
  if [ -z "$archie_python" ] && [ -x /opt/homebrew/opt/python@3.12/bin/python3.12 ]; then archie_python=/opt/homebrew/opt/python@3.12/bin/python3.12; fi
  "${archie_python:-python3}" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.lock
if command -v pnpm >/dev/null 2>&1; then
  (cd apps/web && pnpm install --frozen-lockfile)
else
  (cd apps/web && corepack pnpm install --frozen-lockfile)
fi
if [ ! -f .env ]; then cp .env.example .env; fi
echo 'Ready. Run bash scripts/dev.sh and open http://127.0.0.1:5173/.'
