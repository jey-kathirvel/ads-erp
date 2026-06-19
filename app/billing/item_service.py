from sqlalchemy.orm import Session

from app.billing.item_models import InvoiceItem


class InvoiceItemService:

    @staticmethod
    def create(

        db: Session,

        invoice_id: int,

        product_id: int,

        qty: float,

        rate: float,

        gst_percentage: float,

        total: float

    ):

        taxable = qty * rate

        gst_amount = taxable * gst_percentage / 100

        item = InvoiceItem(

            invoice_id=invoice_id,

            product_id=product_id,

            qty=qty,

            rate=rate,

            discount=0,

            gst_percentage=gst_percentage,

            gst_amount=gst_amount,

            total=total

        )

        db.add(item)

        db.commit()

        db.refresh(item)

        return item