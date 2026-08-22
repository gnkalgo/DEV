# PHASE 4 — Dashboard

## OBJECTIVE

Deliver the protected trading dashboard shell: sidebar layout, widgets, mock-labeled capital, AI signals table structure, order book panel with tick/cancel sounds, IP details modal, and broker configuration form (persist/connect in Phase 5–6).

---

## ARCHITECTURE

```
Login (HttpOnly cookie)
    → ProtectedRoute (/auth/me)
        → AppShell (sidebar)
            → DashboardPage → GET /api/v1/dashboard
            → Broker / Orders / Positions / Settings pages

Order book UI
    → simulate update → play /sounds/order-tick.wav
    → simulate cancel → play /sounds/cancel-tick.wav
    → mute preference in Settings (localStorage)
```

`GET /api/v1/dashboard` returns mock-labeled capital, placeholder signals, empty orders/positions, and config-driven IP details. No broker SDK calls.

---

## API ENDPOINTS

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/dashboard` | authenticated |

---

## FRONTEND ROUTES

| Path | Auth | Purpose |
| --- | --- | --- |
| `/dashboard` | protected | Main widgets + order book |
| `/broker` | protected | Broker form shell |
| `/orders` | protected | Orders table + cancel tick demo |
| `/positions` | protected | Positions table |
| `/settings` | protected | User, env, sound mute |

---

## FILES CREATED

- `backend/app/api/v1/dashboard.py`, `services/dashboard.py`, `schemas/dashboard.py`
- `backend/tests/test_dashboard.py`
- `frontend/src/layouts/AppShell.tsx`, `pages/DashboardPage.tsx`, …
- `frontend/src/components/OrderBookPanel.tsx`, `ProtectedRoute.tsx`, …
- `frontend/public/sounds/order-tick.wav`, `cancel-tick.wav`

---

## SECURITY CHECKLIST

- [x] Dashboard requires session cookie (`/auth/me`)
- [x] No broker secrets in dashboard API response
- [x] Capital explicitly `mock_labeled: true`
- [x] IP details from backend config only
- [x] Sounds play only on explicit order-book actions

## NEXT PHASE

**PHASE 5 — Broker manager + Mock broker** (save/connect, paper orders).
