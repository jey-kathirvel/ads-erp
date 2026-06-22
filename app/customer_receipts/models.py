from datetime import date
from datetime import datetime

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class CustomerReceipt(Base):

    __tablename__ = "customer_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    receipt_no: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )

    customer_id: Mapped[int] = mapped_column(index=True)

    receipt_date: Mapped[date] = mapped_column(Date, default=date.today)

    receipt_mode: Mapped[str | None] = mapped_column(String(30))

    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    remarks: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
