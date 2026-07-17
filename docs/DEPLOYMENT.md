# ADS ERP production deployment

Current Phase 2 path: `/opt/ads-erp-phase2`  
Service: `ads-erp.service`  
URL: `https://erp.ads-ai.in`

## Before deployment

```bash
pg_dump --format=custom --file=/opt/ads-erp/backups/pre-release.dump DATABASE_NAME
git -C /opt/ads-erp-phase2 status -sb
```

Use a timestamped backup filename in real deployments and confirm the backup is readable.

## Deploy tested code

```bash
git -C /opt/ads-erp-phase2 fetch origin
git -C /opt/ads-erp-phase2 pull --ff-only origin develop
/opt/ads-erp-phase2/venv/bin/alembic upgrade head
systemctl restart ads-erp.service
systemctl is-active ads-erp.service
```

## Verify

```bash
curl -I https://erp.ads-ai.in/login
journalctl -u ads-erp.service -n 100 --no-pager
```

Sign in and verify the booking dashboard, online payment requests, booking report and a room-availability search.

## Rollback

Prefer a reviewed Git revert and database restore plan. Do not use `git reset --hard` on production. The prior `/opt/ads-erp` directory is a temporary rollback reference only; production data still requires a compatible database schema.

After Phase 2 approval, consolidate the clean release into the permanent `/opt/ads-erp` path, update the systemd working directory and retain the prior release only for an agreed rollback window.
