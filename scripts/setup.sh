#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.lock
(cd apps/web && npm ci)
if [ ! -f .env ]; then cp .env.example .env; fi
echo 'Ready. Run bash scripts/dev.sh and open http://127.0.0.1:5173/.'
