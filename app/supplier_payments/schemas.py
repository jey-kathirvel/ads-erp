from pydantic import BaseModel


class SupplierPaymentCreate(BaseModel):

    supplier_id: int

    payment_mode: str

    amount: float

    remarks: str = ""