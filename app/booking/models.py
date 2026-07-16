from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class RoomType(Base):

    __tablename__ = "room_types"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    total_rooms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    room_rate: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    rooms: Mapped[list["Room"]] = relationship(
        back_populates="room_type",
    )


class Room(Base):

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)

    room_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    room_type_id: Mapped[int] = mapped_column(
        ForeignKey("room_types.id"),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    room_type: Mapped["RoomType"] = relationship(
        back_populates="rooms",
    )

    booking_rooms: Mapped[list["BookingRoom"]] = relationship(
        back_populates="room",
    )


class Booking(Base):

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)

    booking_no: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    guest_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    mobile: Mapped[str | None] = mapped_column(
        String(20),
        index=True,
    )

    check_in_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    check_out_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    number_of_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    room_type_id: Mapped[int] = mapped_column(
        ForeignKey("room_types.id"),
        nullable=False,
        index=True,
    )

    number_of_rooms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    room_rate: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    advance_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    payment_mode: Mapped[str | None] = mapped_column(
        String(50),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="CONFIRMED",
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    room_type: Mapped["RoomType"] = relationship()

    booking_rooms: Mapped[list["BookingRoom"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
    )


class BookingRoom(Base):

    __tablename__ = "booking_rooms"

    id: Mapped[int] = mapped_column(primary_key=True)

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
        index=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="booking_rooms",
    )

    room: Mapped["Room"] = relationship(
        back_populates="booking_rooms",
    )


class BookingPayment(Base):

    __tablename__ = "booking_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"), nullable=False, unique=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_order_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    provider_payment_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="CAPTURED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    booking: Mapped["Booking"] = relationship()
