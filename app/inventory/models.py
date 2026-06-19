from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class StockTransaction(Base):

    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    transaction_no: Mapped[str | None] = mapped_column(
        String(30)
    )

    transaction_type: Mapped[str | None] = mapped_column(
        String(30)
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    reference_id: Mapped[int | None] = mapped_column(
        Integer
    )

    qty: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    balance_qty: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    remarks: Mapped[str | None] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )