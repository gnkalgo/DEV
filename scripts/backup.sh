#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups
docker compose exec -T postgres pg_dump -U gnkalgo gnkalgo > "backups/gnkalgo-${STAMP}.sql"
echo "Wrote backups/gnkalgo-${STAMP}.sql"
