from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomGSTInvoice(Base):
    __tablename__ = "custom_gst_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_no: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(160), index=True)
    mobile: Mapped[str | None] = mapped_column(String(30), index=True)
    customer_address: Mapped[str | None] = mapped_column(Text)
    customer_gstin: Mapped[str | None] = mapped_column(String(30))
    room_type: Mapped[str] = mapped_column(String(100))
    checkin_date: Mapped[date] = mapped_column(Date)
    checkout_date: Mapped[date] = mapped_column(Date)
    room_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    extra_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
