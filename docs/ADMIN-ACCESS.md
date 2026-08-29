# Admin access — https://www.gnkalgo.com/admin

## URL

**https://www.gnkalgo.com/admin**

You must be **logged in** and your account must have **`is_admin = true`**.

If you see **"Admin only"**, your login email is not an admin yet.

---

## Fix on Oracle server (recommended)

```bash
ssh ubuntu@YOUR_SERVER_IP
cd /opt/gnkalgo
nano .env
```

Add or update (use your real login email):

```env
ADMIN_EMAILS=riyaz.gagguturi@gmail.com
```

Restart backend:

```bash
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
```

On the website:

1. **Sign out**
2. **Login** again with that exact email
3. Open https://www.gnkalgo.com/admin

---

## Fix in database (instant)

```bash
cd /opt/gnkalgo
docker compose -f docker-compose.prod.yml exec postgres psql -U gnkalgo -d gnkalgo
```

```sql
UPDATE users SET is_admin = true WHERE email = 'your-email@gnkalgo.com';
SELECT email, is_admin FROM users WHERE is_admin = true;
```

Then refresh `/admin` (you may need to login again).

---

## What admin can do

- View registered / active / inactive users
- Confirm UPI payments (after customer submits UTR)
- See share link: https://www.gnkalgo.com/subscribe

---

## API URLs (after nginx update)

| URL | Purpose |
|-----|---------|
| https://www.gnkalgo.com/health | Backend health |
| https://www.gnkalgo.com/docs | API documentation |
| https://www.gnkalgo.com/api/v1/ | API index JSON |
| https://www.gnkalgo.com/api/v1/admin/stats | Admin stats (auth + admin) |

If `/health` or `/docs` return 404, update Nginx and rebuild:

```bash
sudo cp /opt/gnkalgo/deploy/nginx/www.gnkalgo.com.conf /etc/nginx/sites-available/
sudo nginx -t && sudo systemctl reload nginx
docker compose -f docker-compose.prod.yml up -d --build
```
