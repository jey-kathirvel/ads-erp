from sqlalchemy.orm import Session

from app.purchase.models import Purchase
from app.purchase.schemas import PurchaseCreate


class PurchaseService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(Purchase)

            .order_by(

                Purchase.id.desc()

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        purchase_id: int

    ):

        return (

            db.query(Purchase)

            .filter(

                Purchase.id == purchase_id

            )

            .first()

        )

    @staticmethod
    def get_items(

        db: Session,

        purchase_id: int

    ):

        from app.purchase.item_models import PurchaseItem

        return (

            db.query(PurchaseItem)

            .filter(

                PurchaseItem.purchase_id == purchase_id

            )

            .all()

        )

    @staticmethod
    def create(

        db: Session,

        data: PurchaseCreate

    ):

        count = db.query(Purchase).count() + 1

        purchase = Purchase(

            purchase_no=f"PUR{count:06}",

            supplier_id=data.supplier_id,

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

        db.add(purchase)

        db.commit()

        db.refresh(purchase)

        return purchase

    @staticmethod
    def delete(

        db: Session,

        purchase_id: int

    ):

        purchase = (

            db.query(Purchase)

            .filter(

                Purchase.id == purchase_id

            )

            .first()

        )

        if purchase:

            db.delete(purchase)

            db.commit()

            return True

        return False