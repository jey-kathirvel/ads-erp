# ADS ERP

FastAPI and PostgreSQL business suite for inventory, billing, purchases, customers, suppliers, accounts, reporting and hotel operations.

## Hotel booking integration

ADS ERP is the inventory authority for Akshat Royal Stay. It shares booking tables with [online-ars](https://github.com/jey-kathirvel/online-ars), preventing staff and public users from allocating the same room for overlapping dates.

Key capabilities:

- Room-type and individual-room management
- Exact 24-hour stays with manual checkout override in ERP
- Live room availability and same-day occupancy
- ERP partial/full payments, including Razorpay
- Online booking source in dashboards and reports
- Five-percent GST pricing
- Ten-minute online payment holds
- ERP countdown for pending online payment
- Automatic `PAYMENT EXPIRED` cancellation and room release
- Guest mobile number and cancellation reason visible to staff
- Full-payment enforcement for public online bookings

## Technology

- Python 3.12, FastAPI, Jinja2 and SQLAlchemy 2
- PostgreSQL 16 and Alembic
- AdminLTE, Bootstrap and application-specific CSS
- Razorpay
- Uvicorn/systemd behind Apache on Ubuntu 24.04

## Quick start

```bash
git clone https://github.com/jey-kathirvel/ads-erp.git
cd ads-erp
git switch develop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload
```

Create the first administrator using the repository bootstrap command documented in [docs/SETUP.md](docs/SETUP.md).

## Documentation

- [Detailed setup](docs/SETUP.md)
- [Phase 2 online-booking integration](docs/ONLINE_BOOKING_INTEGRATION.md)
- [Production deployment](docs/DEPLOYMENT.md)
- [Acceptance testing](docs/BOOKING_TESTING.md)

## Branch workflow

```text
feature branch → develop → VPS acceptance testing → main
```

Database migrations and backups must be reviewed before promotion. Never commit `.env`, database passwords, session secrets or Razorpay credentials.

## Production paths

During Phase 2 testing, ADS ERP runs from `/opt/ads-erp-phase2`. The previous `/opt/ads-erp` release is retained temporarily as a rollback reference and must not receive new development changes.

## Security

- Use strong session and database secrets.
- Keep Razorpay in test mode until acceptance approval.
- Validate Razorpay signature, captured status, currency, order ownership and amount.
- Back up PostgreSQL before every migration.
- Rotate credentials disclosed through chat or screenshots.

## Repository

[github.com/jey-kathirvel/ads-erp](https://github.com/jey-kathirvel/ads-erp)

## Phase 3: booking confirmation email

The booking form accepts an optional guest email. After a staff Razorpay booking is committed, ADS ERP sends a branded confirmation containing the booking, tax, amount paid, balance, and payment reference. A missing email skips delivery; an SMTP failure is logged and never rolls back the confirmed booking.

Configure Hostinger SMTP in `.env` using `.env.example`. Use the mailbox password for `akshatroyalstay@ads-ai.in`, do not commit it, and restart `ads-erp.service` after configuration. The customer-facing terms and refund policy are published by online-ars.

## Hotel invoice workflow

The Custom GST area now provides hotel invoices linked to confirmed bookings.

- Search by the guest's 10-digit mobile number or the final five booking characters. If multiple bookings match, the latest confirmed booking is selected.
- Booking, guest, room, tax, captured payment and balance values are prefilled but remain editable before invoice generation.
- Staff can add multiple named charges, a discount, customer GSTIN/address and payment notes.
- Invoice numbers use the financial-year sequence ARS/YYYY-YY/NNNN.
- The branded invoice supports browser print, a one-page PDF, and email delivery with the PDF attached.
- Property snapshot: Akshat Royal Stay, test GSTIN GSTAKSHATJM81, No. 85 Kamaraj Bazaar Road, Bodinayakanur, Theni District, Tamil Nadu, India - 625513.

Deployment requires alembic upgrade head before restarting ADS ERP. Replace the test GSTIN with the registered GSTIN before production tax invoices are issued.
