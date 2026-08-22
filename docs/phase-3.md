# PHASE 3 — Authentication + Security (start)

## OBJECTIVE

Ship the first working auth path: register, login, logout, `/me`, Argon2 password hashes, server-side sessions with an **HttpOnly** cookie, login rate-limit/lockout, auth audit events, and AES-GCM `encrypt_secret` / `decrypt_secret`. Dashboard widgets and brokers remain later.

---

## ARCHITECTURE

```
POST /api/v1/auth/register → validate → hash password → users → AUTH_REGISTER audit
POST /api/v1/auth/login    → lockout check → verify hash → user_sessions + HttpOnly cookie
POST /api/v1/auth/logout   → revoke session → clear cookie → AUTH_LOGOUT
GET  /api/v1/auth/me       → cookie → hashed session_identifier → UserPublic (no hash)
```

Cookie: `gnkalgo_session` (opaque token). Database stores SHA-256 hex of the token (`session_identifier`, 64 chars). `Secure` is on in production; `SameSite=Lax`.

Redis (non-secret): `rate-limit:login:{email}`, `lockout:login:{email}`.

---

## FILES CREATED / MODIFIED

Backend: `app/core/security.py`, `app/core/errors.py`, `app/utils/validators.py`, `app/utils/encryption.py`, `app/schemas/auth.py`, `app/db/repositories/users.py`, `app/services/auth.py`, `app/api/deps.py`, `app/api/v1/auth.py`, `app/middleware/session.py`, tests, `docs/security.md`.

Frontend: `LoginPage.tsx`, `RegisterPage.tsx`, `services/api.ts` auth helpers.

---

## API ENDPOINTS

| Method | Path | Auth |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | public |
| POST | `/api/v1/auth/login` | public |
| POST | `/api/v1/auth/logout` | authenticated |
| GET | `/api/v1/auth/me` | authenticated |

Password: min 12 chars, upper, lower, digit, symbol. Mobile: Indian 10-digit.

---

## SECURITY CHECKLIST

- [x] Passwords hashed with Argon2; never stored or returned
- [x] HttpOnly session cookie; hashed identifier in PostgreSQL
- [x] Failed login audit + Redis lockout after 5 failures
- [x] `encrypt_secret` / `decrypt_secret` AES-GCM (for later broker ciphertext)
- [x] Nginx CSP header
- [ ] Email verification / TOTP for users (later)
- [ ] Broker connect UI (Phase 4–6)

## NEXT PHASE

**PHASE 4 — Dashboard** — see [phase-4.md](phase-4.md).
