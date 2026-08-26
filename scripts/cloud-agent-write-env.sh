#!/usr/bin/env bash
# Write development .env files for host-based API/UI (Postgres/Redis via published ports).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
BACKEND_ENV="$ROOT/backend/.env"

write_env() {
  cat >"$1" <<'EOF'
APP_NAME="GNK Algo"
APP_ENV=development
DEBUG=true

POSTGRES_USER=gnkalgo
POSTGRES_PASSWORD=password
POSTGRES_DB=gnkalgo

DATABASE_URL=postgresql+asyncpg://gnkalgo:password@127.0.0.1:5432/gnkalgo
REDIS_URL=redis://127.0.0.1:6379/0

JWT_SECRET=dev-jwt-secret-for-cloud-agent
ENCRYPTION_KEY=dev-encryption-key-for-cloud-agent

SESSION_TTL_SECONDS=43200
LOGIN_MAX_FAILURES=5
LOGIN_LOCKOUT_SECONDS=900
SESSION_COOKIE_NAME=gnkalgo_session

TRADING_MODE=PAPER

CORS_ORIGINS=http://localhost:3000,http://localhost

BROKER_API_IP=
SERVER_PUBLIC_IP=
EOF
}

write_env "$ENV_FILE"
write_env "$BACKEND_ENV"
