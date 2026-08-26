#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

set -a
source .env
set +a

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
