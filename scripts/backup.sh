#!/usr/bin/env bash
set -euo pipefail
cd /opt/ads-erp
set -a
source .env
set +a
mkdir -p "${BACKUP_FOLDER:-/opt/ads-erp/backups}"
file="${BACKUP_FOLDER:-/opt/ads-erp/backups}/ads_erp_$(date +%Y%m%d_%H%M%S).dump"
PGPASSWORD="$DB_PASSWORD" "${PG_DUMP_PATH:-/usr/bin/pg_dump}" -U "$DB_USER" -h "$DB_HOST" -Fc "$DB_NAME" -f "$file"
find "${BACKUP_FOLDER:-/opt/ads-erp/backups}" -maxdepth 1 -type f -name 'ads_erp_*.dump' -mtime +30 -delete
