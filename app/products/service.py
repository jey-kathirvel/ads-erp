from sqlalchemy.orm import Session

from app.products.models import Product
from app.products.schemas import ProductCreate


class ProductService:

    @staticmethod
    def get_all(db: Session):

        return (
            db.query(Product)
            .order_by(Product.product_name)
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        product_id: int
    ):

        return (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        data: ProductCreate
    ):

        count = db.query(Product).count() + 1

        product = Product(

            product_code=f"PRD{count:06}",

            product_name=data.product_name,

            category_id=data.category_id,

            unit_id=data.unit_id,

            hsn_code=data.hsn_code,

            gst_percentage=data.gst_percentage,

            purchase_price=data.purchase_price,

            selling_price=data.selling_price,

            opening_stock=data.opening_stock,

            current_stock=data.opening_stock,

            minimum_stock=data.minimum_stock,

            barcode=data.barcode,

            description=data.description

        )

        db.add(product)

        db.commit()

        db.refresh(product)

        return product

    @staticmethod
    def update(
        db: Session,
        product_id: int,
        data: ProductCreate
    ):

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if product is None:

            return None

        product.product_name = data.product_name
        product.category_id = data.category_id
        product.unit_id = data.unit_id
        product.hsn_code = data.hsn_code
        product.gst_percentage = data.gst_percentage
        product.purchase_price = data.purchase_price
        product.selling_price = data.selling_price
        product.opening_stock = data.opening_stock
        product.minimum_stock = data.minimum_stock
        product.barcode = data.barcode
        product.description = data.description

        db.commit()

        db.refresh(product)

        return product

    @staticmethod
    def get_current_stock(
        db: Session
    ):

        return (

            db.query(Product)

            .order_by(

                Product.product_name

            )

            .all()

        )

    @staticmethod
    def get_low_stock(
        db: Session
    ):

        products = ProductService.get_all(db)

        return [

            product

            for product in products

            if float(product.current_stock or 0)
            <= float(product.minimum_stock or 0)

        ]

    @staticmethod
    def get_out_of_stock(
        db: Session
    ):

        products = ProductService.get_all(db)

        return [

            product

            for product in products

            if float(product.current_stock or 0) <= 0

        ]

    @staticmethod
    def update_stock(

        db: Session,

        product_id: int,

        qty: float

    ):

        product = (

            db.query(Product)

            .filter(

                Product.id == product_id

            )

            .first()

        )

        if product:

            current = float(product.current_stock or 0)

            product.current_stock = current - float(qty)

            db.commit()

            db.refresh(product)

            return product

        return None

    @staticmethod
    def stock_in(

        db: Session,

        product_id: int,

        qty: float

    ):

        product = (

            db.query(Product)

            .filter(

                Product.id == product_id

            )

            .first()

        )

        if product:

            current = float(product.current_stock or 0)

            product.current_stock = current + float(qty)

            db.commit()

            db.refresh(product)

            return product

        return None

    @staticmethod
    def delete(
        db: Session,
        product_id: int
    ):

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if product:

            db.delete(product)

            db.commit()

            return True

        return False