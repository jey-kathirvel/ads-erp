from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class CompanySettings(Base):

    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_name: Mapped[str | None] = mapped_column(
        String(200)
    )

    gstin: Mapped[str | None] = mapped_column(
        String(20)
    )

    address: Mapped[str | None] = mapped_column(
        Text
    )

    city: Mapped[str | None] = mapped_column(
        String(100)
    )

    state: Mapped[str | None] = mapped_column(
        String(100)
    )

    pincode: Mapped[str | None] = mapped_column(
        String(20)
    )

    mobile: Mapped[str | None] = mapped_column(
        String(20)
    )

    email: Mapped[str | None] = mapped_column(
        String(100)
    )

    website: Mapped[str | None] = mapped_column(
        String(150)
    )

    invoice_prefix: Mapped[str | None] = mapped_column(
        String(20)
    )

    purchase_prefix: Mapped[str | None] = mapped_column(
        String(20)
    )

    currency: Mapped[str | None] = mapped_column(
        String(20)
    )

    logo: Mapped[str | None] = mapped_column(
        String(255)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )