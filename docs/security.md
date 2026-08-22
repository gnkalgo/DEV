# GNK Algo — Security (Phase 3)

Threat model summary. Do not log or return secrets.

| Threat | Control in Phase 3 |
| --- | --- |
| Stolen password database | Argon2 hashes only (`password_hash`) |
| Session theft from XSS | HttpOnly cookie; CSP on Nginx |
| CSRF | SameSite=Lax; CORS allowlist |
| Brute-force login | Redis failure counter + lockout; dummy hash when the email is unknown |
| Broker secret at rest | `encrypt_secret()` AES-GCM (callers in Phase 5–6) |
| Secret in Redis | Login keys are email/lock flags only |
| LIVE trading by mistake | `TRADING_MODE=PAPER` default unchanged |

Session cookie name: `gnkalgo_session`. Production sets `Secure`. Session TTL default 12 hours (`SESSION_TTL_SECONDS`).

Encryption key: `ENCRYPTION_KEY` (SHA-256 → AES-256-GCM). Production refuses `CHANGE_ME`.
