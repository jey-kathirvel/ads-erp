from pydantic import BaseModel


class CompanySettingCreate(BaseModel):

    company_name: str

    gstin: str = ""

    address: str = ""

    city: str = ""

    state: str = ""

    pincode: str = ""

    mobile: str = ""

    email: str = ""

    website: str = ""

    invoice_prefix: str = "INV"

    purchase_prefix: str = "PUR"

    currency: str = "INR"

    logo: str = ""