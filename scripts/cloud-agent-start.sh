#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./scripts/cloud-agent-dockerd.sh
./scripts/cloud-agent-write-env.sh

docker compose up -d postgres redis

for _ in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U gnkalgo -d gnkalgo >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

cd backend
set -a
source .env
set +a
.venv/bin/alembic upgrade head
