from sqlalchemy.orm import Session

from app.customers.models import Customer
from app.customers.schemas import CustomerCreate
from sqlalchemy.exc import IntegrityError


class CustomerService:

    @staticmethod
    def get_guest_customer(db: Session):

        guest = db.query(Customer).filter(Customer.customer_name == "Guest").first()

        if guest:
            return guest

        last_customer = db.query(Customer).order_by(Customer.id.desc()).first()

        next_no = 1

        if last_customer:
            next_no = last_customer.id + 1

        guest = Customer(
            customer_code=f"CUS{next_no:06}",
            customer_name="Guest",
            contact_person="",
            mobile="",
            email="",
            gstin="",
            address1="",
            address2="",
            city="",
            state="",
            pincode="",
            credit_limit=0,
            opening_balance=0,
        )

        db.add(guest)

        db.commit()

        db.refresh(guest)

        return guest

    @staticmethod
    def create_walkin_customer(db: Session, customer_name: str):

        existing = (
            db.query(Customer).filter(Customer.customer_name == customer_name).first()
        )

        if existing:
            return existing

        last_customer = db.query(Customer).order_by(Customer.id.desc()).first()

        next_no = 1

        if last_customer:
            next_no = last_customer.id + 1

        customer = Customer(
            customer_code=f"CUS{next_no:06}",
            customer_name=customer_name,
            contact_person="",
            mobile="",
            email="",
            gstin="",
            address1="",
            address2="",
            city="",
            state="",
            pincode="",
            credit_limit=0,
            opening_balance=0,
        )

        db.add(customer)

        db.commit()

        db.refresh(customer)

        return customer

    @staticmethod
    def get_all(db: Session):

        return db.query(Customer).order_by(Customer.customer_name).all()

    @staticmethod
    def get_by_id(db: Session, customer_id: int):

        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def create(db: Session, data: CustomerCreate):

        count = db.query(Customer).count() + 1

        customer = Customer(
            customer_code=f"CUS{count:06}",
            customer_name=data.customer_name,
            contact_person=data.contact_person,
            mobile=data.mobile,
            email=data.email,
            gstin=data.gstin,
            address1=data.address1,
            address2=data.address2,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            credit_limit=data.credit_limit,
            opening_balance=data.opening_balance,
        )

        db.add(customer)

        db.commit()

        db.refresh(customer)

        return customer

    @staticmethod
    def update(db: Session, customer_id: int, data: CustomerCreate):

        customer = db.query(Customer).filter(Customer.id == customer_id).first()

        if customer is None:
            return None

        customer.customer_name = data.customer_name
        customer.contact_person = data.contact_person
        customer.mobile = data.mobile
        customer.email = data.email
        customer.gstin = data.gstin
        customer.address1 = data.address1
        customer.address2 = data.address2
        customer.city = data.city
        customer.state = data.state
        customer.pincode = data.pincode
        customer.credit_limit = data.credit_limit
        customer.opening_balance = data.opening_balance

        db.commit()

        db.refresh(customer)

        return customer

@staticmethod
def delete(db: Session, customer_id: int):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        return "not_found"

    try:

        db.delete(customer)

        db.commit()

        return "deleted"

    except IntegrityError:

        db.rollback()

        return "in_use"

    @staticmethod
    def search(db: Session, keyword: str):

        return (
            db.query(Customer)
            .filter(Customer.customer_name.ilike(f"%{keyword}%"))
            .order_by(Customer.customer_name)
            .all()
        )

    @staticmethod
    def get_count(db: Session):

        return db.query(Customer).count()
