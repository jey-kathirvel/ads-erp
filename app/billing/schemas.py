from pydantic import BaseModel


class InvoiceItemCreate(BaseModel):

    product_id: int

    qty: float

    rate: float

    discount: float = 0

    gst_percentage: float = 18

    gst_amount: float = 0

    total: float = 0


class InvoiceCreate(BaseModel):

    customer_id: int

    subtotal: float = 0

    discount: float = 0

    taxable_amount: float = 0

    cgst: float = 0

    sgst: float = 0

    igst: float = 0

    grand_total: float = 0

    payment_mode: str = "Cash"

    remarks: str | None = None

    payment_status: str = "Paid"