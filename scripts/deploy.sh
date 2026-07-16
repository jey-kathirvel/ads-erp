#!/usr/bin/env bash
set -euo pipefail
cd /opt/ads-erp
git fetch origin main
git checkout main
git pull --ff-only origin main
./venv/bin/pip install -r requirements.txt
./venv/bin/alembic upgrade head
sudo systemctl restart ads-erp.service
curl --fail --silent --show-error https://erp.ads-ai.in/health
