from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.booking.models import Booking, BookingRoom, Room


ACTIVE_BOOKING_STATUSES = (
    "RESERVED",
    "CONFIRMED",
    "CHECKED_IN",
)


class BookingService:

    @staticmethod
    def calculate_price(room_rate, number_of_rooms: int, number_of_days: int, gst_percent=5):
        rate = Decimal(str(room_rate))
        subtotal = (rate * number_of_rooms * number_of_days).quantize(Decimal("0.01"))
        gst = (subtotal * Decimal(str(gst_percent)) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return subtotal, gst, subtotal + gst

    @staticmethod
    def calculate_check_out(
        check_in_at: datetime,
        number_of_days: int,
    ) -> datetime:

        if number_of_days < 1:
            raise ValueError("Number of days must be at least 1")

        return check_in_at + timedelta(
            hours=24 * number_of_days
        )

    @staticmethod
    def get_available_rooms(
        db: Session,
        room_type_id: int,
        check_in_at: datetime,
        check_out_at: datetime,
        exclude_booking_id: int | None = None,
    ) -> list[Room]:

        if check_out_at <= check_in_at:
            raise ValueError(
                "Check-out must be after check-in"
            )

        occupied_room_ids_query = (
            db.query(BookingRoom.room_id)
            .join(
                Booking,
                Booking.id == BookingRoom.booking_id,
            )
            .filter(
                Booking.status.in_(
                    ACTIVE_BOOKING_STATUSES
                ),
                BookingRoom.status == "ACTIVE",
                or_(
                    Booking.status != "RESERVED",
                    Booking.payment_expires_at.is_(None),
                    Booking.payment_expires_at > datetime.utcnow(),
                ),
                Booking.check_in_at < check_out_at,
                Booking.check_out_at > check_in_at,
            )
        )

        if exclude_booking_id is not None:
            occupied_room_ids_query = (
                occupied_room_ids_query.filter(
                    Booking.id != exclude_booking_id
                )
            )

        occupied_room_ids = [
            row[0]
            for row in occupied_room_ids_query.all()
        ]

        query = (
            db.query(Room)
            .filter(
                Room.room_type_id == room_type_id,
                Room.is_active.is_(True),
            )
        )

        if occupied_room_ids:
            query = query.filter(
                ~Room.id.in_(occupied_room_ids)
            )

        return (
            query
            .order_by(Room.id)
            .all()
        )

    @staticmethod
    def get_available_count(
        db: Session,
        room_type_id: int,
        check_in_at: datetime,
        check_out_at: datetime,
        exclude_booking_id: int | None = None,
    ) -> int:

        return len(
            BookingService.get_available_rooms(
                db=db,
                room_type_id=room_type_id,
                check_in_at=check_in_at,
                check_out_at=check_out_at,
                exclude_booking_id=exclude_booking_id,
            )
        )
