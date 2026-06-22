from pydantic import BaseModel


class CustomerReceiptCreate(BaseModel):

    customer_id: int

    receipt_mode: str

    amount: float

    remarks: str = ""
