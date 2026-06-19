from sqlalchemy.orm import Session

from app.customer_receipts.models import CustomerReceipt


class CustomerReceiptService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(CustomerReceipt)

            .order_by(

                CustomerReceipt.id.desc()

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        receipt_id: int

    ):

        return (

            db.query(CustomerReceipt)

            .filter(

                CustomerReceipt.id == receipt_id

            )

            .first()

        )

    @staticmethod
    def create(

        db: Session,

        data

    ):

        count = (

            db.query(CustomerReceipt)

            .count()

            + 1

        )

        receipt = CustomerReceipt(

            receipt_no=f"REC{count:06}",

            customer_id=data.customer_id,

            receipt_mode=data.receipt_mode,

            amount=data.amount,

            remarks=data.remarks

        )

        db.add(receipt)

        db.commit()

        db.refresh(receipt)

        return receipt