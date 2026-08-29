# Security baseline

- TLS 1.3 in production (Cloudflare / load balancer)
- Argon2 password hashing
- JWT access 15 minutes, rotating refresh tokens
- TOTP MFA before live trading (enforce in later phase)
- Broker tokens encrypted with Fernet (AES-128-CBC + HMAC via cryptography)
- Webhook tokens + optional HMAC
- Account lockout after 5 failed logins
- Audit log for auth, broker connect, orders
- Dhan order APIs require a static egress IP
- Do not log secrets, tokens, or passwords

AI signals must always show: **Not investment advice.**
