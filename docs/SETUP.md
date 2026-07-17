# ADS ERP setup

## Prerequisites

- Ubuntu 24.04 or a supported local development OS
- Python 3.12+
- PostgreSQL 16
- Git

## Database

Create a PostgreSQL database and user with only the permissions required by ADS ERP. Put connection values in `.env`; do not modify Python source to store credentials.

```bash
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Create an administrator using the supported bootstrap script:

```bash
python create_admin.py
```

Start development mode:

```bash
uvicorn main:app --reload
```

Run unit tests:

```bash
python -m pytest -q
```

E2E tests additionally require Playwright and its browser runtime from `requirements-dev.txt`.

## Shared online inventory

Point `online-ars` at the same PostgreSQL database only after running the Phase 2 Alembic migrations. ERP remains responsible for room types and room records. Both applications must use matching booking-status semantics.
