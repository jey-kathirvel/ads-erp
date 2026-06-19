from pydantic import BaseModel


class SupplierCreate(BaseModel):

    supplier_name: str

    contact_person: str | None = None

    mobile: str | None = None

    email: str | None = None

    gstin: str | None = None

    address1: str | None = None

    address2: str | None = None

    city: str | None = None

    state: str | None = None

    pincode: str | None = None

    opening_balance: float = 0

    is_active: bool = True