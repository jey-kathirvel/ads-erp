from types import SimpleNamespace
from unittest.mock import MagicMock

import app.routes.router  # noqa: F401 - register relationship targets
from app.billing.schemas import InvoiceCreate
from app.billing.service import BillingService


def test_invoice_number_advances_past_existing_invoices():
    db = MagicMock()
    db.query.return_value.all.return_value = [SimpleNamespace(invoice_no="INV000009")]
    invoice = BillingService.create(db, InvoiceCreate(customer_id=1, grand_total=100))
    assert invoice.invoice_no == "INV000010"
    db.add.assert_called_once_with(invoice)
    db.commit.assert_called_once()
