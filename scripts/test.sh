#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
source scripts/runtime.sh
.venv/bin/python scripts/test.py
