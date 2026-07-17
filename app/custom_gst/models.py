from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class CustomGSTInvoice(Base):
    __tablename__ = "custom_gst_invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), nullable=True, index=True) # uniqueness enforced by Alembic partial-safe index
    booking_no: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    invoice_no: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today)
    customer_name: Mapped[str] = mapped_column(String(160), index=True)
    mobile: Mapped[str | None] = mapped_column(String(30), index=True)
    customer_email: Mapped[str | None] = mapped_column(String(254))
    customer_address: Mapped[str | None] = mapped_column(Text)
    customer_gstin: Mapped[str | None] = mapped_column(String(30))
    room_type: Mapped[str] = mapped_column(String(100))
    number_of_rooms: Mapped[int] = mapped_column(Integer, default=1)
    checkin_date: Mapped[date] = mapped_column(Date)
    checkout_date: Mapped[date] = mapped_column(Date)
    room_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    extra_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    additional_items_json: Mapped[str | None] = mapped_column(Text)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=5)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    payment_mode: Mapped[str | None] = mapped_column(String(50))
    payment_reference: Mapped[str | None] = mapped_column(String(120))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
