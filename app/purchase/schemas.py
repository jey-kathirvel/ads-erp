from pydantic import BaseModel


class PurchaseCreate(BaseModel):

    supplier_id: int

    subtotal: float

    discount: float = 0

    taxable_amount: float

    cgst: float

    sgst: float

    igst: float = 0

    grand_total: float

    payment_mode: str

    remarks: str = ""