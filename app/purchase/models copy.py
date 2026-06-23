from datetime import date
from datetime import datetime

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Purchase(Base):

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_no: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))

    purchase_date: Mapped[date] = mapped_column(Date, default=date.today)

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    taxable_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    cgst: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    sgst: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    igst: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    grand_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    payment_mode: Mapped[str | None] = mapped_column(String(30))

    remarks: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
