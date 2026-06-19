from sqlalchemy.orm import Session

from app.billing.models import Invoice
from app.billing.schemas import InvoiceCreate
from app.billing.item_models import InvoiceItem


class BillingService:

    @staticmethod
    def get_all(db: Session):

        return (
            db.query(Invoice)
            .order_by(Invoice.id.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        invoice_id: int
    ):

        return (
            db.query(Invoice)
            .filter(
                Invoice.id == invoice_id
            )
            .first()
        )

    @staticmethod
    def get_items(
        db: Session,
        invoice_id: int
    ):

        return (
            db.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id == invoice_id
            )
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        data: InvoiceCreate
    ):

        count = db.query(Invoice).count() + 1

        invoice = Invoice(

            invoice_no=f"INV{count:06}",

            customer_id=data.customer_id,

            subtotal=data.subtotal,

            discount=data.discount,

            taxable_amount=data.taxable_amount,

            cgst=data.cgst,

            sgst=data.sgst,

            igst=data.igst,

            grand_total=data.grand_total,

            payment_mode=data.payment_mode,

            remarks=data.remarks

        )

        db.add(invoice)

        db.commit()

        db.refresh(invoice)

        return invoice

    @staticmethod
    def delete(
        db: Session,
        invoice_id: int
    ):

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == invoice_id
            )
            .first()
        )

        if invoice:

            db.delete(invoice)

            db.commit()

            return True

        return False