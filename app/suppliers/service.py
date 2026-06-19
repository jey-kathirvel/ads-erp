from sqlalchemy.orm import Session

from app.suppliers.models import Supplier
from app.suppliers.schemas import SupplierCreate


class SupplierService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(Supplier)

            .order_by(

                Supplier.supplier_name

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        supplier_id: int

    ):

        return (

            db.query(Supplier)

            .filter(

                Supplier.id == supplier_id

            )

            .first()

        )

    @staticmethod
    def create(

        db: Session,

        data: SupplierCreate

    ):

        count = db.query(Supplier).count() + 1

        supplier = Supplier(

            supplier_code=f"SUP{count:06}",

            supplier_name=data.supplier_name,

            contact_person=data.contact_person,

            mobile=data.mobile,

            email=data.email,

            gstin=data.gstin,

            address1=data.address1,

            address2=data.address2,

            city=data.city,

            state=data.state,

            pincode=data.pincode,

            opening_balance=data.opening_balance,

            is_active=data.is_active

        )

        db.add(supplier)

        db.commit()

        db.refresh(supplier)

        return supplier

    @staticmethod
    def update(

        db: Session,

        supplier_id: int,

        data: SupplierCreate

    ):

        supplier = (

            db.query(Supplier)

            .filter(

                Supplier.id == supplier_id

            )

            .first()

        )

        if supplier is None:

            return None

        supplier.supplier_name = data.supplier_name
        supplier.contact_person = data.contact_person
        supplier.mobile = data.mobile
        supplier.email = data.email
        supplier.gstin = data.gstin
        supplier.address1 = data.address1
        supplier.address2 = data.address2
        supplier.city = data.city
        supplier.state = data.state
        supplier.pincode = data.pincode
        supplier.opening_balance = data.opening_balance
        supplier.is_active = data.is_active

        db.commit()

        db.refresh(supplier)

        return supplier

    @staticmethod
    def delete(

        db: Session,

        supplier_id: int

    ):

        supplier = (

            db.query(Supplier)

            .filter(

                Supplier.id == supplier_id

            )

            .first()

        )

        if supplier:

            db.delete(supplier)

            db.commit()

            return True

        return False