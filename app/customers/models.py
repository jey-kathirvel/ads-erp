from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Customer(Base):

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    customer_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    contact_person: Mapped[str | None] = mapped_column(
        String(150)
    )

    mobile: Mapped[str | None] = mapped_column(
        String(15),
        index=True
    )

    email: Mapped[str | None] = mapped_column(
        String(150)
    )

    gstin: Mapped[str | None] = mapped_column(
        String(20)
    )

    address1: Mapped[str | None] = mapped_column(
        Text
    )

    address2: Mapped[str | None] = mapped_column(
        Text
    )

    city: Mapped[str | None] = mapped_column(
        String(100)
    )

    state: Mapped[str | None] = mapped_column(
        String(100)
    )

    pincode: Mapped[str | None] = mapped_column(
        String(10)
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="India"
    )

    credit_limit: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    opening_balance: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
