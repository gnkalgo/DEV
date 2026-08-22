# PHASE 5 — Mock broker + paper orders

## OBJECTIVE

Broker manager, encrypted broker persistence, Mock adapter (full PAPER simulation), order service with state machine, and paper order APIs. Default `TRADING_MODE=PAPER`.

---

## ARCHITECTURE

```
React BrokerForm / OrdersPage
    → POST /api/v1/brokers*, /api/v1/orders*
        → BrokerService / OrderService
            → BrokerManager → MockBrokerAdapter (PAPER)
            → ExecutionRouter → PaperExecutor
        → PostgreSQL (broker_accounts, orders, order_events, positions)
        → Redis (broker:session, broker:status, order:idempotency)
```

---

## API ENDPOINTS

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/brokers` | authenticated |
| POST | `/api/v1/brokers` | authenticated |
| POST | `/api/v1/brokers/{id}/connect` | authenticated |
| POST | `/api/v1/brokers/{id}/disconnect` | authenticated |
| POST | `/api/v1/brokers/{id}/test` | authenticated |
| GET | `/api/v1/orders` | authenticated |
| POST | `/api/v1/orders` | authenticated |
| GET | `/api/v1/orders/{id}` | authenticated |
| POST | `/api/v1/orders/{id}/cancel` | authenticated |
| GET | `/api/v1/positions` | authenticated |
| GET | `/api/v1/portfolio` | authenticated |

---

## MOCK BROKER SCENARIOS

| Symbol | Behavior |
| --- | --- |
| `NIFTY`, `RELIANCE`, … | Normal MARKET fill / LIMIT ack |
| `REJECT` | Order rejected |
| `MARGIN_FAIL` | Insufficient margin |
| `MARKET_CLOSED` | Market closed |
| `PARTIAL` | Partial fill |

---

## FILES CREATED

- `backend/app/brokers/` — ABC, MockBrokerAdapter, BrokerManager
- `backend/app/services/broker.py`, `order.py`, `execution.py`, `order_state.py`
- `backend/app/api/v1/brokers.py`, `orders.py`, `positions.py`, `portfolio.py`
- `backend/tests/test_mock_broker.py`, `test_brokers.py`, `test_order_state.py`
- Frontend: wired `BrokerForm`, `OrdersPage`, `api.ts`

---

## SECURITY CHECKLIST

- [x] Credentials encrypted at rest (`encrypt_secret`)
- [x] Access tokens never returned to React
- [x] PAPER default; Mock never places real trades
- [x] Tests use stubs/mocks only

## NEXT PHASE

**PHASE 6 — DhanHQ adapter** (one real broker, official v2 docs only).
