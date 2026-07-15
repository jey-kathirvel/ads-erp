# Architecture hardening rollout

## Production preparation

1. Copy `.env.example` to `.env` and provide production secrets. Never commit `.env`.
2. Install dependencies and run `alembic upgrade head`. For an existing database the baseline is non-destructive.
3. Install `deploy/ads-erp-backup.*` in `/etc/systemd/system/`, then enable the timer.
4. Configure GitHub environment secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`.

## Legacy data migration

Export legacy tables to UTF-8 CSV, copy attachment archives separately, and always run imports with `--dry-run` first. Compare source row counts and financial totals before committing an import. Supported initial datasets are Custom GST invoices, incidents, and finance income. Additional dependent records must be added as explicit importer revisions rather than edited directly in production.

## Alembic policy

The baseline is deliberately non-destructive for existing installations. Every schema change after the baseline requires a reviewed revision. Do not add new `metadata.create_all()` startup hooks.
