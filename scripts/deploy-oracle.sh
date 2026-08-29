#!/usr/bin/env bash
# Deploy GnKAlgo on Oracle VM (pull + docker compose prod rebuild).
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/gnkalgo}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$REPO_DIR"

echo "==> Fetch $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from .env.production.example and configure secrets." >&2
  exit 1
fi

echo "==> Build and start ($COMPOSE_FILE)"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> Status"
docker compose -f "$COMPOSE_FILE" ps

echo "==> Health"
curl -fsS http://127.0.0.1:8000/health || true
echo ""
echo "Deploy complete. Verify https://www.gnkalgo.com/health"
