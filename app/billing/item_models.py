from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class InvoiceItem(Base):

    __tablename__ = "invoice_items"

    product = relationship(
        "Product",
        lazy="joined"
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    qty: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=1
    )

    rate: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    discount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    gst_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=18
    )

    gst_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )
