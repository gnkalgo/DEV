# GNK Algo

Production-oriented algorithmic trading platform for **NSE Equity**, **NSE Futures**, and **NSE Options**.

**Current status: Phase 3 start** (register/login sessions). Dashboard trading widgets and brokers start in later phases.

| Item | Value |
| --- | --- |
| Product | GNK Algo |
| Development | VS Code on Windows 11 |
| Deployment | Ubuntu 24.04 + Docker |
| Default trading mode | `PAPER` (LIVE is never the default) |
| Phase 6 broker | DhanHQ API v2 (official docs only) |

## Architecture

```
Internet → Cloudflare → Nginx → React / FastAPI → Services
    → PostgreSQL + TimescaleDB / Redis
    → BrokerManager → Mock broker or Dhan adapter
```

The browser never calls a broker API, never accesses the database, and never receives broker secrets.

- [docs/architecture.md](docs/architecture.md)
- [docs/phase-0.md](docs/phase-0.md)
- [docs/phase-1.md](docs/phase-1.md)
- [docs/phase-2.md](docs/phase-2.md)
- [docs/phase-3.md](docs/phase-3.md)
- [docs/security.md](docs/security.md)

## Phases

| Phase | Status |
| --- | --- |
| 0 Product definition + architecture | Done |
| 1 Project foundation | Done |
| 2 PostgreSQL + TimescaleDB + Redis | Done |
| 3 Authentication + security | Done (start: register/login/logout/me) |
| 4 Dashboard (logo, order book, tick sounds) | Not started |
| 5 Broker manager + mock broker | Not started |
| 6 DhanHQ adapter (one real broker) | Not started |
| 7–14 Market data, ML, signals, risk, live E2E | Extension points only |

## Prerequisites

- Git
- Docker Desktop (Windows) or Docker Engine (Ubuntu 24.04)
- Optional for local (non-Docker) API/UI: Python 3.11+, Node.js 20+

## Windows (VS Code)

```powershell
cd C:\GNK_IDE
Copy-Item .env.example .env
.\scripts\start.ps1
```

Open http://localhost/

Stop:

```powershell
.\scripts\stop.ps1
```

Health:

```powershell
curl http://localhost/health
curl http://localhost/api/v1/ready
```

## Ubuntu 24.04

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-v2
git clone <your-repo-url> gnkalgo
cd gnkalgo
cp .env.example .env
chmod +x scripts/*.sh
./scripts/start.sh
```

Open http://localhost/

## Docker Compose

```bash
docker compose up -d --build
docker compose logs -f
docker compose down
```

Services: `nginx` (port 80), `frontend`, `backend`, `postgres` (TimescaleDB, `127.0.0.1:5432`), `redis` (`127.0.0.1:6379`).

Do not publish PostgreSQL or Redis on a public interface in production.

## Database migrations

Phase 2 applies OLTP tables and Timescale hypertables.

```powershell
docker compose run --rm --entrypoint alembic backend upgrade head
```

## Testing

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest

cd ..\frontend
npm install
npm test
```

Tests never place live orders and never use real broker credentials.

## Environment variables

Copy [.env.example](.env.example) to `.env`. Never commit `.env`.

Required placeholders to replace before production: `JWT_SECRET`, `ENCRYPTION_KEY`, `POSTGRES_PASSWORD`. Keep `TRADING_MODE=PAPER` unless you intentionally enable live trading in a later phase.

## Security

Never commit PEM/key files, tokens, or broker credentials. Never log passwords, API secrets, TOTP, or access tokens.

## Broker configuration

Not implemented in Phase 1. Phase 5 adds Mock; Phase 6 adds DhanHQ from official documentation only.

## Paper trading

Default mode is PAPER. There is no order execution in Phase 1.

## Production notes

Use Ubuntu 24.04, Docker, a real `.env`, TLS (Cloudflare/Nginx), and do not expose Postgres or Redis publicly. Production refuses `CHANGE_ME` for JWT and encryption keys.

## License

[MIT](LICENSE)
