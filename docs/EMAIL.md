# Email setup for GnKAlgo

Verification emails are sent only when `SMTP_HOST` is set.

Copy `.env.example` to `.env` in the project root (or `backend/.env`) and fill:

| Variable | Example |
|----------|---------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` (STARTTLS) or `465` (SSL) |
| `SMTP_USER` | your mailbox, e.g. `riyaz.gagguturi@gmail.com` |
| `SMTP_PASSWORD` | Gmail **App Password**, not the account password |
| `SMTP_FROM` | same as `SMTP_USER` |
| `SMTP_STARTTLS` | `true` for port 587 |
| `SMTP_SSL` | `true` for port 465 |

## Namecheap Private Email (gnkalgo.com)

```
SMTP_HOST=mail.privateemail.com
SMTP_PORT=465
SMTP_SSL=true
SMTP_STARTTLS=false
SMTP_USER=noreply@gnkalgo.com
SMTP_PASSWORD=<mailbox password in local .env only>
SMTP_FROM=noreply@gnkalgo.com
```

## Gmail

1. Google Account → Security → 2-Step Verification ON  
2. App passwords → generate for Mail  
3. Put the 16-character password in `SMTP_PASSWORD`  
4. Restart the backend (`uvicorn`)

Other hosts: Outlook `smtp.office365.com:587`, Hostinger/GoDaddy use the SMTP host from your DNS/email panel.

Until SMTP is configured, register still shows a **verify link** in the UI so you can continue locally.
