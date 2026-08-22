# PHASE 2 — PostgreSQL + TimescaleDB + Redis

## OBJECTIVE

Create the application schema with **Alembic only**, enable future-ready Timescale hypertables, and add Redis key helpers. Authentication UI, broker adapters, and order execution are **not** implemented yet.

---

## ARCHITECTURE

```
Alembic
    → 0001 baseline (Phase 1, no-op)
    → 0002 OLTP: users, user_sessions, broker_accounts, broker_tokens,
                 orders, order_events, positions, audit_logs
    → 0003 Timescale: market_ticks, market_ohlcv, ml_features,
                      ml_predictions, portfolio_snapshots (hypertables on time)

Redis helpers (cache / locks / idempotency keys only — no secrets)
    latest:ltp:{symbol}
    broker:session:{broker_account_id}
    broker:status:{broker_account_id}
    signal:lock:{symbol}
    order:idempotency:{idempotency_key}
    rate-limit:{user_id}
    ws:presence:{user_id}
```

PostgreSQL remains the system of record. Encrypted broker tokens stay in `broker_tokens`, not Redis. Hypertables have **no writers** until Phase 7+.

---

## FILES CREATED

| File | Purpose |
| --- | --- |
| [backend/app/db/models/](../backend/app/db/models/) | SQLAlchemy 2.x ORM (OLTP + hypertables + enums) |
| [backend/alembic/versions/0002_phase2_oltp.py](../backend/alembic/versions/0002_phase2_oltp.py) | Application tables, FKs, indexes, CHECKs |
| [backend/alembic/versions/0003_phase2_timescale.py](../backend/alembic/versions/0003_phase2_timescale.py) | `timescaledb` extension + `create_hypertable` |
| [backend/app/utils/redis_keys.py](../backend/app/utils/redis_keys.py) | Documented Redis key builders |
| [backend/tests/test_schema.py](../backend/tests/test_schema.py) | Table/index/secret-column contract |
| [backend/tests/test_redis_keys.py](../backend/tests/test_redis_keys.py) | Key shape + secret-payload rejection |
| [backend/tests/test_alembic.py](../backend/tests/test_alembic.py) | Revision chain to `0003_phase2_timescale` |

## FILES MODIFIED

- [README.md](../README.md), [docs/architecture.md](architecture.md), [alembic/env.py](../backend/alembic/env.py) (import models)
- [scripts/start.ps1](../scripts/start.ps1), [scripts/start.sh](../scripts/start.sh) — run `alembic upgrade head` after Compose

## DATABASE CHANGES

OLTP (UUID PKs, `gen_random_uuid()`, timestamptz):

- `users` — unique email/mobile; `password_hash` only
- `user_sessions` — unique `session_identifier`; index `(user_id, expires_at)`
- `broker_accounts` — unique `(user_id, broker, client_id)`; ciphertext columns; status CHECK
- `broker_tokens` — `encrypted_access_token` ciphertext
- `orders` — quantity > 0; side/type/status CHECK; unique `idempotency_key` when present; indexes `(user_id, created_at)`, `(broker_account_id, status)`
- `order_events` — JSONB payload (no secrets)
- `positions` — unique `(broker_account_id, symbol, exchange)`
- `audit_logs` — nullable `user_id`; JSONB `metadata`; indexes on `(user_id, created_at)` and `(event_type, created_at)`

Timescale hypertables on `time` (empty until market/ML phases): `market_ticks`, `market_ohlcv`, `ml_features`, `ml_predictions`, `portfolio_snapshots`.

Do not call `Base.metadata.create_all()` in production.

## API ENDPOINTS

No new HTTP routes. `/ready` still pings PostgreSQL and Redis.

## FRONTEND CHANGES

None.

## ENVIRONMENT VARIABLES

Unchanged. `DATABASE_URL` and `REDIS_URL` from Phase 1.

## INSTALLATION COMMANDS

Windows:

```powershell
cd C:\GNK_IDE
Copy-Item .env.example .env
.\scripts\start.ps1
```

`start.ps1` brings Compose up and runs `alembic upgrade head`.

Manual migrate:

```powershell
docker compose run --rm --entrypoint alembic backend upgrade head
```

## TEST COMMANDS

```powershell
cd C:\GNK_IDE\backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests do not place live orders and do not use broker credentials.

## EXPECTED OUTPUT

- Alembic head is `0003_phase2_timescale`
- Application tables and hypertables exist after migrate
- Pytest includes schema, Redis key, and Alembic chain tests

## SECURITY CHECKLIST

- [x] No plaintext password column
- [x] Broker secrets/tokens stored as encrypted_* columns (encryption helpers still Phase 3/6)
- [x] Redis helpers reject secret field names
- [x] Access tokens not modeled for Redis
- [x] PAPER default unchanged
- [ ] Auth, HttpOnly cookies, encrypt_secret (Phase 3)

## VALIDATION CHECKLIST

- [x] Alembic OLTP tables from architecture §5.1
- [x] Timescale hypertables from architecture §5.2
- [x] Redis key namespaces from architecture §6
- [x] ORM registered in Alembic env
- [ ] User registration (Phase 3)
- [ ] Dashboard (Phase 4)

## KNOWN LIMITATIONS

- No repositories, auth services, or SQL writers besides migrations
- Hypertables are schema-only; no tick/ML ingest
- `encrypt_secret()` is still Phase 3
- Unique `orders.idempotency_key` allows multiple NULLs (PostgreSQL)

## NEXT PHASE

**PHASE 3 — Authentication + security**

Register/login/logout/`/me`, password hashing, HttpOnly sessions, rate limit/lockout, audit on auth events, encryption helpers.
