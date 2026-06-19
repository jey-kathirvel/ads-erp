from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class PurchaseItem(Base):

    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    qty: Mapped[float] = mapped_column(
        Numeric(12,2),
        default=0
    )

    rate: Mapped[float] = mapped_column(
        Numeric(12,2),
        default=0
    )

    gst_percentage: Mapped[float] = mapped_column(
        Numeric(5,2),
        default=0
    )

    total: Mapped[float] = mapped_column(
        Numeric(12,2),
        default=0
    )