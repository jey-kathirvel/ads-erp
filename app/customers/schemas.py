from pydantic import BaseModel
from pydantic import EmailStr


class CustomerCreate(BaseModel):

    customer_name: str

    contact_person: str | None = None

    mobile: str | None = None

    email: EmailStr | None = None

    gstin: str | None = None

    address1: str | None = None

    address2: str | None = None

    city: str | None = None

    state: str | None = None

    pincode: str | None = None

    credit_limit: float = 0

    opening_balance: float = 0
