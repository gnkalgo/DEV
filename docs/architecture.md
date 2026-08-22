# GNK Algo — System Architecture

**Product:** GNK Algo  
**Scope:** NSE Equity, NSE Futures, NSE Options  
**Current implementation phase:** 4 (protected dashboard shell; brokers in Phase 5–6)  
**Primary development:** VS Code on Windows 11  
**Deployment target:** Ubuntu 24.04 + Docker  

This document is the architectural source of truth for Phases 0–6 and the extension points for Phases 7–14. Phase 4 implements the protected dashboard UI and `GET /api/v1/dashboard` mock snapshot.

---

## 1. Product definition

GNK Algo is a production-oriented Indian algorithmic trading platform. Phases **0–6** deliver a runnable full-stack shell:

- Authentication and session security
- Dashboard (including order book UI and tick/cancel audio in Phase 4)
- Encrypted broker configuration
- BrokerManager and broker adapters
- Full Mock broker
- PAPER-default execution
- One real broker adapter: **DhanHQ API v2**

Phases **7–14** (market data engine, feature engine, AI/ML, signals, risk, paper/backtest engines, live execution hardening, production E2E) are **named extension points only**. They are not implemented in Phases 0–6.

AI/ML strategies are **not** built in Phases 0–6. The dashboard may show an AI signals **table shell** with placeholder rows.

### 1.1 Safety rules

- `TRADING_MODE=PAPER` is the default. LIVE requires explicit configuration. Never auto-switch to LIVE.
- The frontend never calls a broker API, never accesses PostgreSQL or Redis, and never receives broker secrets or access tokens.
- Secrets are never logged, never committed to Git, and never returned in API responses.
- Automated tests never place live orders and never use real broker credentials.
- Future ML must never call broker APIs. Path: AI → Signal → Risk Engine → Order Service → Broker Manager → Adapter.
- Never invent broker API endpoints. Unsupported official capabilities return `UNSUPPORTED_OPERATION`.
- Never bypass a future Risk Engine on the live path.
- Never start an automatic trading loop without explicit safeguards (not in scope for 0–6).

---

## 2. System architecture

```
Internet
    |
    v
Cloudflare (DNS, TLS, WAF — production)
    |
    v
Nginx (reverse proxy)
    |-- /            --> React SPA (static)
    |-- /api/        --> FastAPI
    |-- /api/ws/     --> FastAPI WebSocket (Phase 7+)
    |
    v
FastAPI (API layer)
    |
    v
Service layer
    |-- Auth / User / Audit
    |-- Broker / Order / Portfolio
    |
    +--> PostgreSQL + TimescaleDB
    +--> Redis
    |
    v
OrderService
    |
    v
ExecutionMode
    |-- PAPER --> PaperExecutor --> BrokerManager --> MockBrokerAdapter
    |-- LIVE  --> LiveExecutor  --> BrokerManager --> DhanBrokerAdapter
                                              |
                                              +--> TODO adapters (Zerodha, Angel One, Groww, Alice Blue)
```

| Layer | Responsibility |
| --- | --- |
| React + Vite | UI only; Axios/Fetch to `/api/v1` |
| Nginx | SPA + API routing; security headers; request limits; future WebSocket upgrade |
| FastAPI | Thin routers; no direct DB or broker calls in routes |
| Services | Auth, user, broker, order, portfolio, audit |
| Repositories | SQLAlchemy 2.x async persistence |
| PostgreSQL + TimescaleDB | OLTP application data + future hypertables |
| Redis | Cache, session state, rate limit, idempotency, locks — no plaintext secrets |
| BrokerManager | Adapter selection, session, response normalization |
| Adapters | Mock (full), Dhan (official APIs only), other brokers as TODO stubs |

Production must **not** publish PostgreSQL or Redis ports to the public internet. They remain on the Docker/internal network.

---

## 3. Backend architecture

Target layout (created from Phase 1 onward; documented now so later phases do not invent a second structure):

```
backend/app/
    main.py                 FastAPI application factory
    api/v1/                 HTTP routers (thin)
    core/                   config, security, logging, exceptions
    db/                     engine, session, models, repositories
    models/                 domain/ORM entities
    schemas/                Pydantic request/response
    services/               business logic
    brokers/                ABC, manager, mock, adapters
    middleware/             auth, rate limit, request ID
    utils/                  encryption, validators, time
```

### 3.1 Layering rules

- **API layer:** parse HTTP, validate schemas, call one service, map errors to the standard envelope.
- **Service layer:** orchestration, authorization checks, audit, idempotency.
- **Repository layer:** SQL only; no HTTP, no broker SDKs.
- **Broker layer:** only BrokerManager talks to adapters. OrderService never imports a vendor SDK.

### 3.2 Dependency injection

Services receive repositories, Redis, settings, and BrokerManager via FastAPI dependencies. Avoid global mutable state. Settings come from Pydantic Settings + environment (never hard-coded secrets).

### 3.3 Async

Use async SQLAlchemy, async Redis, and async HTTPX for outbound broker HTTP. CPU-heavy work (future ML) runs off the request path.

---

## 4. Frontend architecture

```
Browser
    |
    v
React (TypeScript + Vite + React Router)
    |-- layouts (Header, Sidebar, AppShell)
    |-- pages (login, register, dashboard, broker, orders, positions, settings)
    |-- components (widgets, tables, order book, IP modal)
    |-- services (API client — cookies, no secrets)
    |-- hooks / types / utils
    |
    v
HTTPS /api/v1/*   (Nginx → FastAPI)
```

The UI never holds API keys, TOTP, or access tokens after submit. Stored secrets are displayed only as `************`.

### 4.1 Routes (Phase 4)

| Path | Auth | Purpose |
| --- | --- | --- |
| `/login` | public | Login |
| `/register` | public | Registration |
| `/dashboard` | protected | Market/broker status, capital, P&L, signals shell, order book |
| `/broker` | protected | Broker configuration |
| `/orders` | protected | Order list and paper order actions |
| `/positions` | protected | Positions |
| `/settings` | protected | User and environment display |

### 4.2 Dashboard widgets (Phase 4)

- Header (logo: `frontend/public/brand/logo.png` or SVG when provided)
- Sidebar (responsive: desktop / tablet / mobile)
- Market Status
- Broker Status
- Capital / Margin / Day P&L / Exposure (mock-labeled until a connected broker supplies data)
- Broker Configuration
- AI Signals table **structure only** (Ticker, Segment, AI Trend, Confidence, Strategy State, Entry, SL, Target, Status)
- Positions table
- Orders table
- Order book panel
- IP Details modal (application IP, broker API IP, connection status, last verified, environment — from backend config, not guessed)

### 4.3 Audio (Phase 4)

Short UI sounds, not trading signals:

| Event | Asset (planned) |
| --- | --- |
| Order-book update | `frontend/public/sounds/order-tick.mp3` (or WAV) |
| Order cancel | `frontend/public/sounds/cancel-tick.mp3` (or WAV) |

User mute preference should live in settings (local or account). Sounds must not play on login or background polling without an order-book/cancel event.

### 4.4 Branding

Placeholder path: `frontend/public/brand/logo.png`. Replace when the logo file is supplied. Do not invent a third-party logo.

---

## 5. Database architecture

PostgreSQL is the system of record. TimescaleDB is enabled for future market/ML hypertables. **Alembic** is the only production schema mechanism. Do not use `Base.metadata.create_all()` in production.

### 5.1 Application tables (Phase 2)

#### users

| Column | Notes |
| --- | --- |
| id | UUID PK |
| email | unique, indexed, not null |
| mobile | unique, indexed, not null |
| full_name | not null |
| password_hash | not null; never store plaintext |
| is_active | default true |
| is_verified | default false (activation flag) |
| created_at / updated_at | timestamptz |

#### user_sessions

| Column | Notes |
| --- | --- |
| id | UUID PK |
| user_id | FK users.id ON DELETE CASCADE |
| session_identifier | unique, indexed (opaque) |
| expires_at | not null |
| revoked_at | nullable |
| created_at | timestamptz |

Index: `(user_id, expires_at)`.

#### broker_accounts

| Column | Notes |
| --- | --- |
| id | UUID PK |
| user_id | FK users.id |
| broker | enum/string: MOCK, DHAN, ZERODHA, ANGEL_ONE, GROWW, ALICE_BLUE |
| client_id | broker client id (not a secret by itself, still treat carefully) |
| encrypted_api_key | bytea/text ciphertext |
| encrypted_api_secret | ciphertext |
| encrypted_totp | ciphertext |
| status | DISCONNECTED, CONNECTING, CONNECTED, ERROR |
| created_at / updated_at | timestamptz |

Unique: `(user_id, broker, client_id)`.

#### broker_tokens

| Column | Notes |
| --- | --- |
| id | UUID PK |
| broker_account_id | FK broker_accounts.id ON DELETE CASCADE |
| encrypted_access_token | ciphertext; never sent to React |
| token_expires_at | timestamptz |
| created_at / updated_at | timestamptz |

#### orders

| Column | Notes |
| --- | --- |
| id | UUID PK |
| user_id | FK users.id |
| broker_account_id | FK broker_accounts.id |
| symbol, exchange, segment | normalized |
| side | BUY / SELL |
| order_type | MARKET / LIMIT / SL / SL-M (mapped per adapter) |
| quantity | positive int |
| price | nullable |
| status | see order state machine |
| broker_order_id | nullable, indexed |
| idempotency_key | unique where present |
| created_at / updated_at | timestamptz |

Indexes: `(user_id, created_at)`, `(broker_account_id, status)`.

#### order_events

| Column | Notes |
| --- | --- |
| id | UUID PK |
| order_id | FK orders.id ON DELETE CASCADE |
| event_type | state transition name |
| payload | JSONB (no secrets) |
| created_at | timestamptz |

#### positions

| Column | Notes |
| --- | --- |
| id | UUID PK |
| user_id | FK users.id |
| broker_account_id | FK |
| symbol, exchange | |
| quantity, average_price | |
| realized_pnl, unrealized_pnl | |
| updated_at | timestamptz |

Unique: `(broker_account_id, symbol, exchange)` (refine if product type requires a wider key).

#### audit_logs

| Column | Notes |
| --- | --- |
| id | UUID PK |
| user_id | FK nullable for unauthenticated events |
| event_type | |
| ip_address | inet or text |
| user_agent | text |
| metadata | JSONB (redacted) |
| created_at | timestamptz |

Index: `(user_id, created_at)`, `(event_type, created_at)`.

### 5.2 Future Timescale tables (schemas only until Phase 7+)

These may be created as empty/future-ready hypertables. No ML engine writes them in 0–6.

- `market_ticks` — hypertable on time
- `market_ohlcv` — hypertable on time
- `ml_features`
- `ml_predictions`
- `portfolio_snapshots`

---

## 6. Redis architecture

Redis is **not** the system of record for orders, users, or credentials.

| Purpose | Example key | Value (non-secret) |
| --- | --- | --- |
| LTP cache | `latest:ltp:{symbol}` | JSON quote |
| Broker session flag | `broker:session:{broker_account_id}` | connected/expiry metadata |
| Broker status | `broker:status:{broker_account_id}` | CONNECTED / DISCONNECTED / ERROR |
| Future signal lock | `signal:lock:{symbol}` | lock token |
| Order idempotency | `order:idempotency:{idempotency_key}` | order id |
| Rate limit | `rate-limit:{user_id}` | counter |
| Future WebSocket | `ws:presence:{user_id}` | connection id |

Do not store API secrets, TOTP, or access tokens in Redis unless encrypted **and** strictly necessary. Prefer encrypted tokens in PostgreSQL (`broker_tokens`).

---

## 7. Authentication architecture

```
Register --> validate --> hash password --> users row --> audit
Login    --> rate limit --> verify hash --> lockout/delay --> session + HttpOnly cookie --> audit
Logout   --> revoke session --> clear cookie --> audit
/me      --> cookie/session --> user DTO (no password hash)
```

### 7.1 Endpoints (Phase 3)

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Registration validates full name, email, mobile, password, confirm_password; rejects duplicate email/mobile; enforces strong passwords; never stores plaintext.

Login creates a server-side session (`user_sessions`) plus a secure HttpOnly cookie (`Secure` in production, `SameSite` set). Failed logins are audited and rate-limited with progressive delay or lockout.

Protected routes use authentication middleware and a current-user dependency. Unauthenticated requests return 401.

---

## 8. Broker architecture

```
React
    --> FastAPI /api/v1/brokers*
        --> BrokerService (encrypt, persist, never return secrets)
            --> BrokerManager
                --> BrokerAdapter (ABC)
                    --> MockBrokerAdapter        (Phase 5, mandatory)
                    --> DhanBrokerAdapter        (Phase 6, official DhanHQ v2 only)
                    --> ZerodhaKiteAdapter       TODO
                    --> AngelOneAdapter          TODO
                    --> GrowwAdapter             TODO
                    --> AliceBlueAdapter         TODO
```

### 8.1 BrokerAdapter (ABC)

Async methods:

- `authenticate()`
- `refresh_session()`
- `disconnect()`
- `get_ltp()`
- `get_ohlcv()`
- `get_option_chain()`
- `get_margin()`
- `get_positions()`
- `get_holdings()`
- `place_order()`
- `modify_order()`
- `cancel_order()`
- `get_order_status()`

The rest of the application depends only on these methods and **normalized** models.

### 8.2 Normalized models

**Quote**

```json
{
  "symbol": "NIFTY",
  "exchange": "NSE",
  "ltp": 0,
  "timestamp": "2026-08-22T06:00:00+00:00"
}
```

**Order (internal request)**

```json
{
  "symbol": "NIFTY",
  "exchange": "NSE",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": 1,
  "price": null
}
```

**OrderResponse**

```json
{
  "success": true,
  "broker_order_id": "...",
  "status": "SUBMITTED"
}
```

Vendor payloads are mapped into this format inside the adapter. Unknown vendor fields are dropped or stored only in `order_events.payload` without secrets.

### 8.3 Broker configuration UI

Dropdown:

- Mock (development / PAPER)
- Dhan (Phase 6 implementation)
- Zerodha Kite (TODO)
- Angel One (TODO)
- Groww (TODO)
- Alice Blue (TODO)

Fields: Client ID, API Key, API Secret, TOTP Token. Sent only over HTTPS in production. Backend encrypts before storage. Existing records show `************` for secrets. Actions: Save Broker, Test Connection, Connect, Disconnect.

Access tokens **never** return to React.

### 8.4 DhanHQ v2 contract (Phase 6)

Official documentation only:

- Authentication: [https://dhanhq.co/docs/v2/authentication/](https://dhanhq.co/docs/v2/authentication/)
- Orders: [https://dhanhq.co/docs/v2/orders/](https://dhanhq.co/docs/v2/orders/)
- Python SDK (optional wrap of documented APIs): [https://github.com/dhan-oss/DhanHQ-py](https://github.com/dhan-oss/DhanHQ-py)

Facts used for design (do not invent additional URLs):

- Every request uses an **access token** (`access-token` header).
- Individuals can generate a token on [web.dhan.co](https://web.dhan.co) or use API Key/Secret with OAuth/consent or PIN+TOTP via the official login flow.
- Order place/modify/cancel uses `https://api.dhan.co/v2/orders` and requires **static IP whitelist**.
- Fetching some order/trade details may not require IP whitelist (per vendor docs).
- Implement LTP, OHLCV, option chain, margin, positions **only if documented**. Otherwise return `UNSUPPORTED_OPERATION`.
- Trading APIs vs Data APIs: some market-data calls may require a Dhan Data API subscription; document this in Phase 6 adapter comments.

Connect flow:

```
User --> Broker Configuration --> Connect
    --> Broker Authentication (Dhan token / OAuth / PIN+TOTP as officially supported)
    --> Encrypted access token in broker_tokens
    --> Active session metadata in Redis (non-secret)
```

---

## 9. Paper / live execution architecture

```
OrderService
    --> validate + idempotency + persist CREATED
    --> ExecutionMode (from config; default PAPER)
        |-- PAPER --> PaperExecutor --> MockBrokerAdapter
        |-- LIVE  --> LiveExecutor  --> BrokerManager --> real adapter (Dhan)
```

- Default: `TRADING_MODE=PAPER`.
- LIVE must be an explicit environment/config choice, not a UI accident.
- Tests always force PAPER and Mock.
- Mock broker simulates: success, reject, insufficient margin, market closed, invalid quantity, partial fill, cancel. It never places real trades.

---

## 10. Order service and state machine

OrderService (not routers) performs: input validation, quantity/type/symbol checks, idempotency, audit, persistence, submission via ExecutionMode.

### 10.1 States

`CREATED` → `VALIDATING` → `APPROVED` → `SUBMITTED` → `ACKNOWLEDGED` → `PARTIALLY_FILLED` → `FILLED`

Also: `CANCEL_REQUESTED` → `CANCELLED`  
Terminal: `REJECTED`, `FAILED`, `EXPIRED`

### 10.2 Allowed transitions

| From | To |
| --- | --- |
| CREATED | VALIDATING, REJECTED, FAILED |
| VALIDATING | APPROVED, REJECTED, FAILED |
| APPROVED | SUBMITTED, REJECTED, FAILED |
| SUBMITTED | ACKNOWLEDGED, REJECTED, FAILED, EXPIRED |
| ACKNOWLEDGED | PARTIALLY_FILLED, FILLED, CANCEL_REQUESTED, REJECTED, EXPIRED |
| PARTIALLY_FILLED | PARTIALLY_FILLED, FILLED, CANCEL_REQUESTED, EXPIRED |
| CANCEL_REQUESTED | CANCELLED, FILLED, PARTIALLY_FILLED, FAILED |
| FILLED, CANCELLED, REJECTED, FAILED, EXPIRED | (terminal) |

Illegal transitions are rejected and audited.

---

## 11. API design

Version prefix: `/api/v1/`

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/health` and `/api/v1/health` | public |
| GET | `/ready` and `/api/v1/ready` | public (checks DB + Redis) |
| GET | `/` | public (API metadata) |
| POST | `/api/v1/auth/register` | public |
| POST | `/api/v1/auth/login` | public |
| POST | `/api/v1/auth/logout` | authenticated |
| GET | `/api/v1/auth/me` | authenticated |
| GET | `/api/v1/brokers` | authenticated |
| POST | `/api/v1/brokers` | authenticated |
| POST | `/api/v1/brokers/{id}/connect` | authenticated |
| POST | `/api/v1/brokers/{id}/disconnect` | authenticated |
| POST | `/api/v1/brokers/{id}/test` | authenticated |
| GET | `/api/v1/portfolio` | authenticated |
| GET | `/api/v1/positions` | authenticated |
| GET | `/api/v1/orders` | authenticated |
| POST | `/api/v1/orders` | authenticated |
| GET | `/api/v1/orders/{id}` | authenticated |
| POST | `/api/v1/orders/{id}/cancel` | authenticated |
| GET | `/api/v1/dashboard` | authenticated |

Health body:

```json
{
  "status": "ok",
  "service": "gnkalgo-api"
}
```

Do not add endpoints that have no service implementation.

### 11.1 Error envelope

```json
{
  "success": false,
  "error": {
    "code": "BROKER_NOT_CONNECTED",
    "message": "Broker is not connected"
  }
}
```

HTTP usage: 400, 401, 403, 404, 409, 422, 429, 500, 503. No stack traces in production.

---

## 12. Security architecture

Threat model (summary; full write-up in `docs/security.md` from Phase 3):

| Threat | Control |
| --- | --- |
| Credential theft at rest | Authenticated encryption (`ENCRYPTION_KEY`); secrets never in Git |
| Credential theft in transit | TLS (production); HTTPS-only cookies |
| XSS stealing session | HttpOnly cookies; CSP; no secrets in JS |
| CSRF | SameSite cookies; CORS allowlist |
| Brute-force login | Rate limit + lockout/progressive delay |
| SSRF / broker abuse from browser | Browser cannot reach brokers |
| Log leakage | Structured logs; redaction of password, API secret, TOTP, tokens |
| Live order in tests/CI | PAPER + Mock only in tests |
| Invented broker APIs | Adapters call documented endpoints only |

Security headers via Nginx + FastAPI middleware. Input validation via Pydantic. Audit logging for auth and order events.

Encryption helpers (Phase 3/6): `encrypt_secret()` / `decrypt_secret()` using authenticated encryption.

---

## 13. Logging

Structured logs with: request ID, user ID (when authenticated), endpoint, latency, status, broker operation name, internal order ID.

Never log: password, API secret, TOTP, access/refresh tokens.

Correlation IDs propagate from Nginx/`X-Request-ID` through FastAPI middleware.

---

## 14. Future AI/ML, market data, and risk (extension points only)

Do not implement these services in Phases 0–6. Reserve module names and interfaces:

| Phase | Interface | May call |
| --- | --- | --- |
| 7 | `MarketDataService` | Redis LTP keys, Timescale ticks/OHLCV, broker `get_ltp`/`get_ohlcv` via BrokerManager |
| 8 | `FeatureEngineeringService` | market tables only |
| 9 | `MLModelService` | features; writes `ml_predictions` |
| 10 | `SignalService` | predictions → normalized signals |
| 11 | `RiskEngine` | signals + positions + margin; **required before live orders** |
| 12 | `BacktestEngine`, `PaperTradingEngine` | historical data; Mock/PAPER |
| 13 | `LiveExecutionEngine` | OrderService after RiskEngine |
| 14 | Production E2E, observability | all of the above |

Future data/ML libraries (Pandas, NumPy, Polars, SciPy, LightGBM, XGBoost, PyTorch, VectorBT, Backtrader) are **not** installed in Phases 0–6 unless a non-ML need appears.

```
AI / MLModelService
    --> SignalService
        --> RiskEngine
            --> OrderService
                --> BrokerManager
                    --> BrokerAdapter
                        --> Broker API
```

---

## 15. Deployment architecture

```
Ubuntu 24.04 host
    Docker Compose network (internal)
        nginx          published 80/443
        frontend       not public (nginx only)
        backend        not public (nginx only)
        postgres       volume persist; not published in production
        redis          AOF/RDB as configured; not published in production
```

Compose services (Phase 1): backend, frontend, postgres (Timescale image), redis, nginx. Healthchecks, restart policies, volumes, internal network.

Nginx:

- `/api/` → FastAPI
- `/` → React
- Security headers, request body limits, proxy timeouts
- WebSocket upgrade headers reserved for Phase 7+
- Server names prepared: `gnkalgo.com`, `app.gnkalgo.com`, `api.gnkalgo.com`
- **Do not hard-code production IP addresses**

Environment (planned `.env.example` in Phase 1): `APP_NAME`, `APP_ENV`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `TRADING_MODE=PAPER`, `CORS_ORIGINS`, `BROKER_API_IP`, `SERVER_PUBLIC_IP`. Never commit `.env`.

DX: Makefile on Unix; `scripts/start.ps1`, `stop.ps1`, `test.ps1` on Windows. Also `scripts/start.sh`, `stop.sh`, `healthcheck.sh`, `backup.sh`.

---

## 16. Testing strategy (from Phase 1)

- Backend: unit, API, DB, auth, BrokerManager, Mock, OrderService, state machine.
- Frontend: login, register, protected routes, dashboard, broker form, orders, positions, logout.
- E2E paper flow: register → login → dashboard → add Mock → connect → capital/positions → PAPER order → status → logout. **Never a real order.**

---

## 17. Repository layout (target)

Repository root is this workspace (`GNK_IDE`), not a nested `gnkalgo/` folder.

```
backend/     frontend/     nginx/     docker/     scripts/     tests/e2e/     docs/
.env.example  .gitignore    docker-compose.yml    README.md    LICENSE
```

Phase 0 creates only `docs/architecture.md`, `docs/phase-0.md`, `README.md`, and `LICENSE`.

---

## 18. Design decisions

1. **PAPER default** — live trading is opt-in and adapter-gated.
2. **Single real broker in Phase 6: Dhan** — other names remain UI + TODO to avoid invented APIs.
3. **Thin API, fat services** — routes never touch SQLAlchemy or vendor SDKs.
4. **Encrypt at rest** — broker credentials and tokens in PostgreSQL ciphertext.
5. **Timescale later** — enable extension early; hypertables unused until market data.
6. **Windows + Ubuntu** — PowerShell scripts alongside POSIX scripts.
7. **Logo and ticks are Phase 4 assets** — paths reserved; files supplied later.
