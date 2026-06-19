# ADS ERP

<div align="center">

# 🚀 ADS ERP

### Modern ERP Solution built with FastAPI + PostgreSQL

Inventory • Billing • Purchase • Customers • Suppliers • Accounts • Reports

</div>

---

# Features

## Authentication

- User Login
- Logout
- Session Management
- Route Protection

## Dashboard

- Customer Count
- Product Count
- Invoice Count
- Low Stock Alert
- Inventory Value
- Recent Transactions

## Company

- Company Settings
- GST Information
- Invoice Prefix
- Purchase Prefix

## Customer Management

- Customer Master
- Search
- Edit
- Delete

## Product Management

- Product Master
- Categories
- Units
- GST
- HSN
- Barcode
- Stock Management

## Inventory

- Current Stock
- Low Stock
- Stock Transactions
- Stock Dashboard

## Billing

- Sales Invoice
- Invoice History
- GST Ready

## Purchase

- Purchase Entry
- Supplier Management

## Reports

- Sales Reports
- Inventory Reports
- Customer Reports

---

# Technology Stack

| Technology | Version |
|----------------|------------|
| Python | 3.12 |
| FastAPI | Latest |
| PostgreSQL | 16 |
| SQLAlchemy | 2.x |
| Jinja2 | Latest |
| Bootstrap | 5 |
| AdminLTE | 3 |

---

# Project Structure

```
ads-erp
│
├── app/
│   ├── accounts/
│   ├── auth/
│   ├── billing/
│   ├── categories/
│   ├── company/
│   ├── config/
│   ├── customers/
│   ├── dashboard/
│   ├── inventory/
│   ├── products/
│   ├── purchase/
│   ├── reports/
│   ├── routes/
│   ├── suppliers/
│   ├── supplier_payments/
│   ├── templates/
│   └── static/
│
├── database/
├── docs/
├── requirements.txt
├── main.py
└── README.md
```

---

# Installation

## Clone Repository

```
git clone https://github.com/<username>/ads-erp.git

cd ads-erp
```

---

## Create Virtual Environment

```
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```
pip install -r requirements.txt
```

---

## Configure Database

Create PostgreSQL database

```
createdb ads_erp_db
```

Update

```
app/config/database.py
```

---

## Run

```
uvicorn main:app --reload
```

Open

```
http://localhost:8000
```

---

# Production

Using

- Ubuntu 24
- Gunicorn/Uvicorn
- Apache Reverse Proxy
- PostgreSQL

---

# Future Roadmap

- Multi Company
- Multi Branch
- POS Billing
- Barcode Printing
- WhatsApp Invoice
- GST Return
- Email Invoice
- Audit Logs
- API Integration

---

# Screenshots

Coming Soon

---

# License

MIT License

---

# Author

ADS Digital Solutions

Website

https://ads-ai.in

---

# Support

For issues and feature requests, please create an issue in GitHub.
