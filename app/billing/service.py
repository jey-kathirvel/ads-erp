from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.billing.models import Invoice
from app.billing.schemas import InvoiceCreate
from app.billing.item_models import InvoiceItem


class BillingService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(Invoice)

            .options(

                joinedload(Invoice.customer)

            )

            .order_by(

                Invoice.id.desc()

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        invoice_id: int

    ):

        return (

            db.query(Invoice)

            .options(

                joinedload(Invoice.customer)

            )

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

            .options(

                joinedload(InvoiceItem.product)

            )

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

            remarks=data.remarks,

            status="Completed"

        )

        db.add(invoice)

        db.commit()

        db.refresh(invoice)

        return invoice

    @staticmethod
    def update(

        db: Session,

        invoice_id: int,

        data: InvoiceCreate,

        product_id: list[int],

        qty: list[float],

        rate: list[float],

        gst: list[float],

        total: list[float]

    ):

        invoice = (

            db.query(Invoice)

            .filter(

                Invoice.id == invoice_id

            )

            .first()

        )

        if invoice is None:

            return None

        # -----------------------------
        # Update Invoice Header
        # -----------------------------

        invoice.customer_id = data.customer_id

        invoice.subtotal = data.subtotal

        invoice.discount = data.discount

        invoice.taxable_amount = data.taxable_amount

        invoice.cgst = data.cgst

        invoice.sgst = data.sgst

        invoice.igst = data.igst

        invoice.grand_total = data.grand_total

        invoice.payment_mode = data.payment_mode

        invoice.remarks = data.remarks

        db.commit()

        # -----------------------------
        # Delete Existing Items
        # -----------------------------

        db.query(

            InvoiceItem

        ).filter(

            InvoiceItem.invoice_id == invoice_id

        ).delete()

        db.commit()

        # -----------------------------
        # Insert Updated Items
        # -----------------------------

        for i in range(len(product_id)):

            item = InvoiceItem(

                invoice_id=invoice_id,

                product_id=product_id[i],

                qty=qty[i],

                rate=rate[i],

                gst_percentage=gst[i],

                total=total[i]

            )

            db.add(item)

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

            (

                db.query(

                    InvoiceItem

                )

                .filter(

                    InvoiceItem.invoice_id == invoice_id

                )

                .delete()

            )

            db.delete(invoice)

            db.commit()

            return True

        return False