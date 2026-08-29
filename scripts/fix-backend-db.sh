#!/usr/bin/env bash
# Diagnose and restart GnKAlgo backend DB connectivity on Oracle VM.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/gnkalgo}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
cd "$REPO_DIR"

echo "==> Compose status"
docker compose -f "$COMPOSE_FILE" ps

echo "==> Recent backend logs"
docker compose -f "$COMPOSE_FILE" logs backend --tail 60 || true

echo "==> Postgres ready?"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-gnkalgo}" || true

echo "==> Postgres login test (uses POSTGRES_* from .env)"
set -a
# shellcheck disable=SC1091
source .env
set +a
if docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT 1 AS ok;'; then
  echo "Postgres auth OK with current .env password"
else
  echo "Postgres auth FAILED — POSTGRES_PASSWORD does not match the volume."
  echo "Fix: put the original password back in .env, OR reset the volume (wipes data):"
  echo "  docker compose -f $COMPOSE_FILE down"
  echo "  docker volume ls | grep postgres"
  echo "  docker volume rm <postgres_volume_name>"
  echo "  docker compose -f $COMPOSE_FILE up -d --build"
  exit 1
fi

echo "==> Rebuild/restart backend"
docker compose -f "$COMPOSE_FILE" up -d --build backend
sleep 8
docker compose -f "$COMPOSE_FILE" logs backend --tail 40
curl -fsS http://127.0.0.1:8000/health && echo " health OK" || echo " health FAILED"
