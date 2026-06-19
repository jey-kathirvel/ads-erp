from sqlalchemy.orm import Session

from app.settings.models import CompanySettings


class CompanyService:

    @staticmethod
    def get(db: Session):

        return (

            db.query(CompanySettings)

            .first()

        )
@staticmethod
def get_company(db: Session):

    return (

        db.query(CompanySettings)

        .first()

    )
    @staticmethod
    def save(

        db: Session,

        company

    ):

        existing = (

            db.query(CompanySettings)

            .first()

        )

        if existing:

            existing.company_name = company.company_name
            existing.gstin = company.gstin
            existing.address = company.address
            existing.city = company.city
            existing.state = company.state
            existing.pincode = company.pincode
            existing.mobile = company.mobile
            existing.email = company.email
            existing.website = company.website
            existing.logo = company.logo

            db.commit()

            db.refresh(existing)

            return existing

        db.add(company)

        db.commit()

        db.refresh(company)

        return company