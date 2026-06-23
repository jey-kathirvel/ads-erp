from sqlalchemy.orm import Session

from app.purchase.item_models import PurchaseItem
from app.products.models import Product
from app.inventory.models import StockTransaction


class PurchaseItemService:

    @staticmethod
    def create(
        db: Session,
        purchase_id: int,
        product_id: int,
        qty: float,
        rate: float,
        gst_percentage: float,
        total: float,
    ):

        item = PurchaseItem(
            purchase_id=purchase_id,
            product_id=product_id,
            qty=qty,
            rate=rate,
            gst_percentage=gst_percentage,
            total=total,
        )

        db.add(item)

        db.commit()

        db.refresh(item)

        product = db.query(Product).filter(Product.id == product_id).first()

        if product:

            current_stock = float(product.current_stock or 0)

            new_stock = current_stock + float(qty)

            product.current_stock = new_stock

            db.commit()

            stock = StockTransaction(
                transaction_no=f"PUR-{purchase_id}",
                transaction_type="PURCHASE",
                product_id=product_id,
                reference_id=purchase_id,
                qty=qty,
                balance_qty=new_stock,
                remarks="Purchase Entry",
            )

            db.add(stock)

            db.commit()

            db.refresh(stock)

        return item

    @staticmethod
    def get_items(db: Session, purchase_id: int):

        return (
            db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
        )

    @staticmethod
    def delete_items(db: Session, purchase_id: int):

        items = (
            db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
        )

        for item in items:

            db.delete(item)

        db.commit()

        return True

    @staticmethod
    def rollback_stock(db: Session, purchase_id: int):

        items = (
            db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
        )

        for item in items:

            product = db.query(Product).filter(Product.id == item.product_id).first()

            if product:

                current_stock = float(product.current_stock or 0)

                new_stock = current_stock - float(item.qty)

                if new_stock < 0:

                    new_stock = 0

                product.current_stock = new_stock

                stock = StockTransaction(
                    transaction_no=f"PUR-DEL-{purchase_id}",
                    transaction_type="PURCHASE_DELETE",
                    product_id=item.product_id,
                    reference_id=purchase_id,
                    qty=-float(item.qty),
                    balance_qty=new_stock,
                    remarks="Purchase Deleted",
                )

                db.add(stock)

        db.commit()

        return True
