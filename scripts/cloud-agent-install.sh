#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! python3 -c "import venv" 2>/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv
fi

test -f .env || cp .env.example .env
python3 -m venv backend/.venv
backend/.venv/bin/pip install -q -r backend/requirements.txt
if [ -f backend/requirements-dev.txt ]; then
  backend/.venv/bin/pip install -q -r backend/requirements-dev.txt
fi
npm ci --prefix frontend --prefer-offline
