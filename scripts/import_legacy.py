"""Idempotent CSV importer for applications migrated into ADS ERP.

Usage: python scripts/import_legacy.py custom-gst exports/invoices.csv --dry-run
       python scripts/import_legacy.py incidents exports/incidents.csv
       python scripts/import_legacy.py finance-income exports/income.csv
"""
import argparse
import csv
from datetime import date, datetime
from decimal import Decimal

from app.config.database import SessionLocal
from app.custom_gst.models import CustomGSTInvoice
from app.finance_tools.models import FinanceIncome
from app.incidents.models import Incident


def decimal(value): return Decimal(str(value or 0))
def parsed_date(value): return date.fromisoformat(value[:10])


def custom_gst(row):
    return CustomGSTInvoice(invoice_no=row["invoice_no"], customer_name=row["customer_name"], mobile=row.get("mobile") or None,
        customer_address=row.get("customer_address") or None, customer_gstin=row.get("customer_gstin") or None,
        room_type=row["room_type"], checkin_date=parsed_date(row["checkin_date"]), checkout_date=parsed_date(row["checkout_date"]),
        room_charge=decimal(row.get("room_charge")), extra_charge=decimal(row.get("extra_charge")),
        gst_percent=decimal(row.get("gst_percent")), gst_amount=decimal(row.get("gst_amount")), total_amount=decimal(row.get("total_amount")))


def incident(row):
    return Incident(case_no=row["case_no"], subject=row["subject"], description=row.get("description") or None,
        category=row.get("category") or "Other", priority=row.get("priority") or "Medium", status=row.get("status") or "Open",
        room_no=row.get("room_no") or None, hotel_area=row.get("hotel_area") or None, guest_name=row.get("guest_name") or None,
        guest_mobile=row.get("guest_mobile") or None, created_by_name=row.get("created_by_name") or "Legacy Import")


def finance_income(row):
    return FinanceIncome(income_date=parsed_date(row["income_date"]), category=row["category"], amount=decimal(row["amount"]),
        payment_mode=row.get("payment_mode") or "Cash", reference_no=row.get("reference_no") or None,
        received_from=row["received_from"], description=row.get("description") or None, created_by_name="Legacy Import")


CONFIG = {
    "custom-gst": (CustomGSTInvoice, "invoice_no", custom_gst),
    "incidents": (Incident, "case_no", incident),
    "finance-income": (FinanceIncome, "reference_no", finance_income),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=CONFIG)
    parser.add_argument("csv_file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    model, key, factory = CONFIG[args.dataset]
    db = SessionLocal(); inserted = skipped = failed = 0
    try:
        with open(args.csv_file, newline="", encoding="utf-8-sig") as handle:
            for number, row in enumerate(csv.DictReader(handle), 2):
                try:
                    with db.begin_nested():
                        value = row.get(key)
                        if value and db.query(model).filter(getattr(model, key) == value).first(): skipped += 1; continue
                        db.add(factory(row)); db.flush(); inserted += 1
                except Exception as exc:
                    failed += 1; print(f"row {number}: {exc}")
        if args.dry_run: db.rollback()
        else: db.commit()
    finally: db.close()
    print({"dataset": args.dataset, "inserted": inserted, "skipped": skipped, "failed": failed, "dry_run": args.dry_run})
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__": main()
