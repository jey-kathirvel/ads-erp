from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Supplier(Base):

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    supplier_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    supplier_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )

    contact_person: Mapped[str | None] = mapped_column(
        String(100)
    )

    mobile: Mapped[str | None] = mapped_column(
        String(20),
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
        String(20)
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