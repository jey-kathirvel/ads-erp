from sqlalchemy.orm import Session

from app.supplier_payments.models import SupplierPayment


class SupplierPaymentService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(SupplierPayment)

            .order_by(

                SupplierPayment.id.desc()

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        payment_id: int

    ):

        return (

            db.query(SupplierPayment)

            .filter(

                SupplierPayment.id == payment_id

            )

            .first()

        )

    @staticmethod
    def create(

        db: Session,

        data

    ):

        count = (

            db.query(SupplierPayment)

            .count()

            + 1

        )

        payment = SupplierPayment(

            payment_no=f"PAY{count:06}",

            supplier_id=data.supplier_id,

            payment_mode=data.payment_mode,

            amount=data.amount,

            remarks=data.remarks

        )

        db.add(payment)

        db.commit()

        db.refresh(payment)

        return payment