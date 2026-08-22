# PHASE 6 — DhanHQ adapter

## OBJECTIVE

One real broker integration using **official DhanHQ API v2 documentation only**. LIVE trading requires explicit `TRADING_MODE=LIVE`. Static IP whitelist is required for order placement APIs per vendor rules.

---

## OFFICIAL DOCUMENTATION

- Authentication: https://dhanhq.co/docs/v2/authentication/
- Orders: https://dhanhq.co/docs/v2/orders/

---

## IMPLEMENTED

| Capability | Endpoint / flow |
| --- | --- |
| Profile / test | `GET https://api.dhan.co/v2/profile` |
| Token (TOTP) | `POST https://auth.dhan.co/app/generateAccessToken` |
| Renew token | `POST https://api.dhan.co/v2/RenewToken` |
| Place order | `POST https://api.dhan.co/v2/orders` |
| Modify order | `PUT https://api.dhan.co/v2/orders/{order-id}` |
| Cancel order | `DELETE https://api.dhan.co/v2/orders/{order-id}` |
| Order status | `GET https://api.dhan.co/v2/orders/{order-id}` |

### Unsupported (returns `UNSUPPORTED_OPERATION`)

- `get_ltp`, `get_ohlcv`, `get_option_chain`, `get_margin`, `get_positions`, `get_holdings`

Market data may require a separate Dhan Data API subscription per vendor documentation.

---

## CONNECT FLOW

1. Save broker (`POST /api/v1/brokers`) with client ID and optional API key (trading PIN) + TOTP.
2. Connect (`POST /api/v1/brokers/{id}/connect`) with optional one-time `access_token` from [web.dhan.co](https://web.dhan.co).
3. Token encrypted into `broker_tokens`; session metadata in Redis (non-secret).
4. LIVE orders require `security_id` on order create (Dhan scrip ID).

---

## FILES

- `backend/app/brokers/dhan.py`
- `backend/tests/test_dhan_adapter.py` (httpx mocked — no live calls)

---

## SECURITY CHECKLIST

- [x] Official URLs only — no invented endpoints
- [x] LIVE gated by `TRADING_MODE=LIVE`
- [x] Access tokens encrypted; never in API responses
- [x] Other brokers remain TODO stubs in UI

## NEXT PHASE

**PHASE 7** — Market data ingestion (extension point).
