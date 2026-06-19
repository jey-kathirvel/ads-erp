from sqlalchemy.orm import Session

from app.inventory.models import StockTransaction
from app.products.models import Product


class InventoryService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(StockTransaction)

            .order_by(

                StockTransaction.id.desc()

            )

            .all()

        )

    @staticmethod
    def get_current_stock(db: Session):

        return (

            db.query(Product)

            .order_by(

                Product.product_name

            )

            .all()

        )

    @staticmethod
    def get_low_stock(db: Session):

        return (

            db.query(Product)

            .filter(

                Product.current_stock <= Product.minimum_stock

            )

            .all()

        )

    @staticmethod
    def create(

        db: Session,

        transaction_no,

        transaction_type,

        product_id,

        reference_id,

        qty,

        balance_qty,

        remarks

    ):

        stock = StockTransaction(

            transaction_no=transaction_no,

            transaction_type=transaction_type,

            product_id=product_id,

            reference_id=reference_id,

            qty=qty,

            balance_qty=balance_qty,

            remarks=remarks

        )

        db.add(stock)

        db.commit()

        db.refresh(stock)

        return stock