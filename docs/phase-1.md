# PHASE 1 — Project Foundation

## OBJECTIVE

Create a runnable GNK Algo development environment: FastAPI, Vite/React, PostgreSQL (Timescale image), Redis, Nginx, Docker Compose, health/readiness probes, and developer scripts. Authentication, schema tables, brokers, and the trading dashboard are **not** implemented yet.

---

## ARCHITECTURE

```
Browser
    → Nginx :80
        → / and SPA          → frontend container
        → /api/, /health, /ready → backend :8000 FastAPI
            → ping PostgreSQL + TimescaleDB
            → ping Redis
```

PAPER remains the default `TRADING_MODE`. PostgreSQL and Redis are published only on `127.0.0.1` for local development, not on the public interface.

---

## FILES TO CREATE / CREATED

Backend application factory, settings, health router, async SQLAlchemy engine, Redis client, Alembic baseline, pytest, Dockerfiles, Compose, Nginx, scripts, Phase 1 frontend shell.

## FILES MODIFIED

- [README.md](../README.md) — install and Docker commands
- [docs/architecture.md](architecture.md) — current phase marker

## DATABASE CHANGES

Alembic revision `0001_phase1_baseline` is a no-op. **No application tables.** TimescaleDB is available because Compose uses `timescale/timescaledb:latest-pg16`. Hypertables and OLTP tables arrive in Phase 2.

## API ENDPOINTS

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/` | API metadata, includes `trading_mode` |
| GET | `/health` | `{"status":"ok","service":"gnkalgo-api"}` |
| GET | `/api/v1/health` | same |
| GET | `/ready` | 200 if DB + Redis ping; 503 otherwise |
| GET | `/api/v1/ready` | same |

## FRONTEND CHANGES

Vite + React + TypeScript + React Router. Home page calls `/api/v1/health` and `/api/v1/ready`. Later routes are placeholders. Placeholder wordmark: `frontend/public/brand/logo.svg` (replace when the real logo is provided).

## ENVIRONMENT VARIABLES

See [.env.example](../.env.example). Copy to `.env` (never commit). Change `JWT_SECRET` and `ENCRYPTION_KEY` before any production deployment.

## INSTALLATION COMMANDS

Windows (VS Code, PowerShell):

```powershell
cd C:\GNK_IDE
Copy-Item .env.example .env
.\scripts\start.ps1
```

Then open http://localhost/

Ubuntu 24.04:

```bash
cd /opt/gnkalgo   # or your clone path
cp .env.example .env
chmod +x scripts/*.sh
./scripts/start.sh
```

Local API without Nginx (optional, after Compose DB is up):

```powershell
cd C:\GNK_IDE\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+asyncpg://gnkalgo:password@127.0.0.1:5432/gnkalgo"
$env:REDIS_URL="redis://127.0.0.1:6379/0"
uvicorn app.main:app --reload --port 8000
```

Frontend dev server (proxies `/api` to port 8000):

```powershell
cd C:\GNK_IDE\frontend
npm install
npm run dev
```

Alembic (no tables yet):

```powershell
docker compose run --rm --no-deps --entrypoint alembic backend upgrade head
```

## TEST COMMANDS

```powershell
cd C:\GNK_IDE\backend
python -m pytest
cd C:\GNK_IDE\frontend
npm install
npm test
```

Or: `.\scripts\test.ps1` (backend tests via Compose).

## EXPECTED OUTPUT

- `GET /health` → `{"status":"ok","service":"gnkalgo-api"}`
- `GET /ready` → `status: ok` with database and redis checks when Compose is healthy
- Frontend at http://localhost/ shows Phase 1 foundation and health status
- Pytest and Vitest pass without contacting any broker

## SECURITY CHECKLIST

- [x] `.env` gitignored; `.env.example` has placeholders only
- [x] No broker credentials in source
- [x] `TRADING_MODE` defaults to PAPER
- [x] Postgres/Redis bound to localhost in Compose
- [x] Nginx security headers present
- [x] Production start refuses `CHANGE_ME` JWT/encryption keys
- [ ] Auth, encryption of broker secrets, rate limit (Phase 3+)

## VALIDATION CHECKLIST

- [x] FastAPI health endpoints
- [x] Ready checks DB + Redis
- [x] React + Vite + Router
- [x] Docker Compose: backend, frontend, postgres, redis, nginx
- [x] Alembic wired (baseline only)
- [x] Windows and bash scripts
- [ ] Full user registration (Phase 3)
- [ ] Dashboard (Phase 4)

## KNOWN LIMITATIONS

- No users, sessions, orders, or broker adapters
- `/ready` requires running Postgres and Redis (or returns 503)
- Logo is a temporary SVG wordmark
- Tick/cancel audio still Phase 4
- Frontend tests mock the API
- Compose `env_file: .env` requires copying `.env.example` first

## NEXT PHASE

**PHASE 2 — PostgreSQL + TimescaleDB + Redis**

Alembic migrations for `users`, `user_sessions`, `broker_accounts`, `broker_tokens`, `orders`, `order_events`, `positions`, `audit_logs`, plus future-ready Timescale hypertables. Redis key helpers. Still no auth UI or live trading.
