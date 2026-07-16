from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FinanceCategory(Base):
    __tablename__ = "finance_expense_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(20), default="#2563eb")
    icon: Mapped[str] = mapped_column(String(50), default="fas fa-receipt")
    display_order: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinanceVendor(Base):
    __tablename__ = "finance_vendors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    mobile: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    gstin: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinanceIncome(Base):
    __tablename__ = "finance_income"
    id: Mapped[int] = mapped_column(primary_key=True)
    income_date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_mode: Mapped[str] = mapped_column(String(50), default="Cash")
    reference_no: Mapped[str | None] = mapped_column(String(100))
    received_from: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    attachment: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_by_name: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinanceExpense(Base):
    __tablename__ = "finance_expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    expense_date: Mapped[date] = mapped_column(Date, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("finance_expense_categories.id"), index=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("finance_vendors.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_mode: Mapped[str] = mapped_column(String(50), default="Cash")
    bill_number: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    attachment: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="Paid")
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_by_name: Mapped[str | None] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    category = relationship("FinanceCategory", lazy="joined")
    vendor = relationship("FinanceVendor", lazy="joined")


class FinanceQuotation(Base):
    __tablename__ = "finance_quotations"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_no: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255))
    vendor_gst: Mapped[str | None] = mapped_column(String(30))
    vendor_phone: Mapped[str | None] = mapped_column(String(30))
    vendor_email: Mapped[str | None] = mapped_column(String(255))
    quotation_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    remarks: Mapped[str | None] = mapped_column(Text)
    attachment: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_by_name: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    items = relationship("FinanceQuotationItem", cascade="all, delete-orphan", back_populates="quotation")


class FinanceQuotationItem(Base):
    __tablename__ = "finance_quotation_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("finance_quotations.id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=1)
    unit: Mapped[str | None] = mapped_column(String(30))
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gst: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    quotation = relationship("FinanceQuotation", back_populates="items")
