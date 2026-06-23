from sqlalchemy.orm import Session

from app.company.models import CompanySetting
from app.company.schemas import CompanySettingCreate


class CompanyService:

    @staticmethod
    def get(db: Session):

        return db.query(CompanySetting).first()

    @staticmethod
    def save(db: Session, data: CompanySettingCreate):

        company = db.query(CompanySetting).first()

        if company is None:

            company = CompanySetting()

            db.add(company)

        company.company_name = data.company_name
        company.gstin = data.gstin
        company.address = data.address
        company.city = data.city
        company.state = data.state
        company.pincode = data.pincode
        company.mobile = data.mobile
        company.email = data.email
        company.website = data.website
        company.invoice_prefix = data.invoice_prefix
        company.purchase_prefix = data.purchase_prefix
        company.currency = data.currency
        company.logo = data.logo

        db.commit()

        db.refresh(company)

        return company
