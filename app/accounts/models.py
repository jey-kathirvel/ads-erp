from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Account(Base):

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    account_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    account_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    account_group: Mapped[str] = mapped_column(String(100), nullable=False)

    opening_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LedgerEntry(Base):

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    voucher_no: Mapped[str | None] = mapped_column(String(30))

    voucher_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account_id: Mapped[int] = mapped_column(nullable=False, index=True)

    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    remarks: Mapped[str | None] = mapped_column(Text)

    reference_type: Mapped[str | None] = mapped_column(String(50))

    reference_id: Mapped[int | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
