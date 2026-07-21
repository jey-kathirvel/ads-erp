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
from app.booking.models import Booking, Room


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

    room = relationship(Room)


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

    room = relationship(Room)
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


class HotelLaundryBatch(Base):
    __tablename__ = "hotel_laundry_batches"
    __table_args__ = (
        UniqueConstraint(
            "batch_no",
            name="uq_hotel_laundry_batches_batch_no",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    batch_no: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        unique=True,
        index=True,
    )

    batch_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ROOM",
        index=True,
    )

    room_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "rooms.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "bookings.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="COLLECTED",
        index=True,
    )

    vendor_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    expected_return_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    total_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    clean_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    damaged_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    missing_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    room = relationship(Room)

    booking = relationship(Booking)

    items: Mapped[list["HotelLaundryBatchItem"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class HotelLaundryBatchItem(Base):
    __tablename__ = "hotel_laundry_batch_items"
    __table_args__ = (
        UniqueConstraint(
            "laundry_batch_id",
            "inventory_item_id",
            name="uq_hotel_laundry_batch_item",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    laundry_batch_id: Mapped[int] = mapped_column(
        ForeignKey(
            "hotel_laundry_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "hotel_inventory_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    issued_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    returned_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    clean_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    damaged_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    missing_quantity: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    batch: Mapped["HotelLaundryBatch"] = relationship(
        back_populates="items",
    )

    inventory_item: Mapped["HotelInventoryItem"] = relationship()

