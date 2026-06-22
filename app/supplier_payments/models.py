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


class SupplierPayment(Base):

    __tablename__ = "supplier_payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    payment_no: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )

    supplier_id: Mapped[int] = mapped_column(index=True)

    payment_date: Mapped[date] = mapped_column(Date, default=date.today)

    payment_mode: Mapped[str | None] = mapped_column(String(30))

    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    remarks: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
