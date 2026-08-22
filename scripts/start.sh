#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — change CHANGE_ME secrets before production."
fi
docker compose up -d --build
docker compose run --rm --entrypoint alembic backend upgrade head
