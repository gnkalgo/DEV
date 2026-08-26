#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/cloud-agent-*.sh scripts/*.sh

./scripts/cloud-agent-dockerd.sh
./scripts/cloud-agent-write-env.sh

docker compose up -d postgres redis

for _ in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U gnkalgo -d gnkalgo >/dev/null 2>&1 \
    && docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    break
  fi
  sleep 1
done

if ! python3 -c "import venv" 2>/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv
fi

cd backend
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
set -a
source .env
set +a
.venv/bin/alembic upgrade head

cd "$ROOT/frontend"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
