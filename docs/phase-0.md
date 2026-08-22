# PHASE 0 — Product Definition and Architecture

## OBJECTIVE

Define GNK Algo as a production-oriented NSE Equity / Futures / Options platform, lock the layered architecture, safety rules, and Phase 1–6 / 7–14 boundaries **before any application code**.

This phase produces documentation only. Nothing is runnable yet.

---

## ARCHITECTURE

See [architecture.md](architecture.md) for the full design.

Summary:

```
Internet → Cloudflare → Nginx → React / FastAPI → Services
    → PostgreSQL + TimescaleDB / Redis
    → OrderService → ExecutionMode (PAPER default | LIVE explicit)
        → BrokerManager → Mock | Dhan | TODO adapters
```

Future (not implemented): AI → Signal → RiskEngine → OrderService → BrokerManager → Adapter.

---

## FILES CREATED

| File | Purpose |
| --- | --- |
| [docs/architecture.md](architecture.md) | System, backend, frontend, database, Redis, auth, broker, security, paper/live, future ML/market data/risk, deployment |
| [docs/phase-0.md](phase-0.md) | This phase record |
| [README.md](../README.md) | Product intro; Phase 0 status |
| [LICENSE](../LICENSE) | MIT |

## FILES MODIFIED

None (empty repository).

---

## FULL SOURCE CODE

Not applicable. Phase 0 is documentation.

---

## DATABASE CHANGES

Logical schema specified in architecture.md. **No Alembic, no `CREATE TABLE`, no Timescale hypertables applied.**

---

## API ENDPOINTS

Catalogued in architecture.md. **None implemented.**

---

## FRONTEND CHANGES

UX reserved: dashboard routes, order book, tick/cancel audio paths, logo path `frontend/public/brand/logo.png`. **No React app yet.**

---

## ENVIRONMENT VARIABLES

Planned for Phase 1 `.env.example` (do not commit `.env`):

```
APP_NAME=GNK Algo
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://gnkalgo:password@postgres:5432/gnkalgo
REDIS_URL=redis://redis:6379/0
JWT_SECRET=CHANGE_ME
ENCRYPTION_KEY=CHANGE_ME
TRADING_MODE=PAPER
CORS_ORIGINS=http://localhost:3000
BROKER_API_IP=
SERVER_PUBLIC_IP=
```

---

## DESIGN DECISIONS

1. Repository root is this workspace (`GNK_IDE`), not a nested `gnkalgo/` directory.
2. Phase 6 real broker is **DhanHQ API v2** only. Official docs: [authentication](https://dhanhq.co/docs/v2/authentication/), [orders](https://dhanhq.co/docs/v2/orders/). SDK reference: [DhanHQ-py](https://github.com/dhan-oss/DhanHQ-py). No invented endpoints.
3. Broker dropdown will include Mock, Dhan, Zerodha Kite, Angel One, Groww, Alice Blue. Only Mock (Phase 5) and Dhan (Phase 6) get real adapters; others are TODO stubs returning `UNSUPPORTED_OPERATION` or “not implemented”.
4. `TRADING_MODE=PAPER` is the default. LIVE is never the default and never auto-enabled.
5. Frontend never talks to brokers, PostgreSQL, or Redis and never receives access tokens or API secrets.
6. Alembic is the only production migration path.
7. Redis holds cache, session flags, rate limits, idempotency, and locks — not plaintext secrets.
8. Logo and audio files are specified as paths; you will supply the logo later. Sounds are Phase 4.
9. ML libraries are not installed in Phases 0–6.
10. Implementation is gated: Phase N+1 does not start until Phase N is validated.

---

## INSTALLATION COMMANDS

Phase 0 has nothing to install.

To review docs on Windows (VS Code):

```powershell
cd C:\GNK_IDE
code docs\architecture.md
code docs\phase-0.md
code README.md
```

---

## TEST COMMANDS

None. Validation is a documentation review (checklist below).

---

## EXPECTED OUTPUT

- Four files exist at the paths listed above.
- Architecture describes Cloudflare → Nginx → React/FastAPI → services → Postgres/Timescale/Redis → BrokerManager.
- Dhan is named as the only Phase 6 live adapter, with official documentation links.
- PAPER is documented as default.

---

## SECURITY CHECKLIST

- [x] Secrets policy documented (no Git, no logs, no React)
- [x] PAPER default documented
- [x] Tests must not use live credentials (documented)
- [x] Encryption at rest planned (`ENCRYPTION_KEY`)
- [x] Dhan static IP requirement for order APIs documented
- [ ] Encryption helpers implemented (Phase 3/6)
- [ ] HttpOnly cookies implemented (Phase 3)
- [ ] Security headers in Nginx (Phase 1/4)

---

## VALIDATION CHECKLIST

- [x] Product name: GNK Algo
- [x] Markets: NSE Equity, Futures, Options
- [x] Layered architecture documented
- [x] Broker path documented (no browser → broker)
- [x] Future AI path documented (no ML → broker)
- [x] Database tables listed with keys/index intent
- [x] Redis key namespaces listed
- [x] Order state machine and transitions listed
- [x] API map listed
- [x] Phase 7–14 named as extension points only
- [x] Windows 11 + Ubuntu 24.04 deployment targets documented
- [x] Logo/audio paths reserved
- [ ] Stakeholder sign-off to start Phase 1

---

## KNOWN LIMITATIONS

- Application is not runnable (no FastAPI, React, Docker, Postgres, Redis).
- Logo file is not in the repository yet.
- Tick/cancel audio files are not in the repository yet.
- Dhan live trading still requires a real account, access token (or API key flow), possible Data API subscription, and static IP whitelist — documented, not implemented.
- GitHub remote is not created until requested.
- `docs/security.md`, `database-design.md`, `broker-design.md`, `deployment.md`, and `phase-1.md` … `phase-6.md` are planned for later phases (architecture.md already covers those topics at Phase 0 depth).

---

## NEXT PHASE

**PHASE 1 — Project Foundation**

Create the repository skeleton: FastAPI (`GET /health`, `GET /ready`, `GET /`), Vite React+TypeScript, Docker Compose (backend, frontend, postgres with Timescale, redis, nginx), `.env.example`, `.gitignore`, Windows PowerShell scripts + Makefile/sh scripts.

Do not implement authentication, brokers, or the dashboard until Phase 1 is validated.
