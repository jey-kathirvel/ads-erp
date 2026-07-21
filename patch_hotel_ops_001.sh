#!/usr/bin/env bash
set -euo pipefail

cd /opt/ads-erp-phase2 || exit 1

CURRENT_BRANCH="$(git branch --show-current)"
if [ "$CURRENT_BRANCH" != "ui-buttons" ]; then
    echo "ERROR: Current branch is '$CURRENT_BRANCH'. Switch to ui-buttons first."
    exit 1
fi

echo "===== PATCH-HOTEL-OPS-001 START ====="

mkdir -p app/hotel_operations
cp -a main.py "main.py.patch-hotel-ops-001.bak"

cat > app/hotel_operations/__init__.py <<'PY'
# Hotel operations package.
PY

cat > app/hotel_operations/models.py <<'PY'
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HotelStaff(Base):
    __tablename__ = "hotel_staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    staff_code: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    staff_name: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    department: Mapped[str] = mapped_column(
        String(30), nullable=False, default="HOUSEKEEPING", index=True
    )
    designation: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    housekeeping_tasks: Mapped[list["HousekeepingTask"]] = relationship(
        back_populates="staff",
    )


class HotelRoomStatus(Base):
    __tablename__ = "hotel_room_status"
    __table_args__ = (
        UniqueConstraint("room_id", name="uq_hotel_room_status_room_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="VACANT_CLEAN",
        index=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    room = relationship("Room")


class HousekeepingTask(Base):
    __tablename__ = "housekeeping_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("hotel_staff.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CLEANING",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NORMAL",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    room = relationship("Room")
    staff: Mapped["HotelStaff | None"] = relationship(
        back_populates="housekeeping_tasks",
    )


class HotelInventoryItem(Base):
    __tablename__ = "hotel_inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_code: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    item_name: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    unit: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Nos"
    )
    minimum_stock: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    current_stock: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    transactions: Mapped[list["HotelInventoryTransaction"]] = relationship(
        back_populates="inventory_item",
        cascade="all, delete-orphan",
    )


class HotelInventoryTransaction(Base):
    __tablename__ = "hotel_inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey("hotel_inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    balance_after: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    reference_no: Mapped[str | None] = mapped_column(
        String(60), nullable=True, index=True
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    inventory_item: Mapped["HotelInventoryItem"] = relationship(
        back_populates="transactions",
    )
PY

python3 - <<'PY'
from pathlib import Path

path = Path("main.py")
text = path.read_text()

import_line = (
    "from app.hotel_operations.models import (\n"
    "    HotelInventoryItem,\n"
    "    HotelInventoryTransaction,\n"
    "    HotelRoomStatus,\n"
    "    HotelStaff,\n"
    "    HousekeepingTask,\n"
    ")\n"
)

if "from app.hotel_operations.models import (" not in text:
    anchor = "from app.booking.models import BookingPayment\n"
    if anchor not in text:
        raise SystemExit("ERROR: BookingPayment import anchor not found")
    text = text.replace(anchor, anchor + import_line, 1)

startup_block = (
    "\n\n@app.on_event(\"startup\")\n"
    "def ensure_hotel_operations_tables():\n"
    "    # Create only hotel operations tables.\n"
    "    HotelStaff.metadata.create_all(\n"
    "        bind=engine,\n"
    "        tables=[\n"
    "            HotelStaff.__table__,\n"
    "            HotelRoomStatus.__table__,\n"
    "            HousekeepingTask.__table__,\n"
    "            HotelInventoryItem.__table__,\n"
    "            HotelInventoryTransaction.__table__,\n"
    "        ],\n"
    "        checkfirst=True,\n"
    "    )\n"
)

if "def ensure_hotel_operations_tables" not in text:
    anchor = "# ----------------------------------------------------\n# Home\n# ----------------------------------------------------"
    if anchor not in text:
        raise SystemExit("ERROR: Home section anchor not found")
    text = text.replace(anchor, startup_block + "\n" + anchor, 1)

path.write_text(text)
PY

echo "===== COMPILE VERIFY ====="
./venv/bin/python -m compileall app main.py

echo "===== MODEL IMPORT VERIFY ====="
./venv/bin/python - <<'PY'
from app.hotel_operations.models import (
    HotelInventoryItem,
    HotelInventoryTransaction,
    HotelRoomStatus,
    HotelStaff,
    HousekeepingTask,
)

assert HotelStaff.__tablename__ == "hotel_staff"
assert HotelRoomStatus.__tablename__ == "hotel_room_status"
assert HousekeepingTask.__tablename__ == "housekeeping_tasks"
assert HotelInventoryItem.__tablename__ == "hotel_inventory_items"
assert HotelInventoryTransaction.__tablename__ == "hotel_inventory_transactions"

print("MODEL IMPORTS: PASSED")
PY

echo "===== GIT VERIFY ====="
git diff --check
git diff --stat

echo
echo "PATCH-HOTEL-OPS-001 CODE INSTALLED"
echo
echo "NEXT COMMANDS:"
echo "git add app/hotel_operations main.py"
echo 'git commit -m "Add hotel operations database foundation"'
echo "git push origin ui-buttons"
echo "systemctl restart ads-erp"
echo "systemctl status ads-erp --no-pager"
