from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Product(Base):

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id")
    )

    unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("units.id")
    )

    hsn_code: Mapped[str | None] = mapped_column(
        String(20)
    )

    gst_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=18
    )

    purchase_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    selling_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    opening_stock: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    current_stock: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    minimum_stock: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100)
    )

    image: Mapped[str | None] = mapped_column(
        String(255)
    )

    description: Mapped[str | None] = mapped_column(
        Text
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