from pydantic import BaseModel


class ProductCreate(BaseModel):

    product_name: str

    category_id: int | None = None

    unit_id: int | None = None

    hsn_code: str | None = None

    gst_percentage: float = 18

    purchase_price: float = 0

    selling_price: float = 0

    opening_stock: float = 0

    minimum_stock: float = 0

    barcode: str | None = None

    description: str | None = None
