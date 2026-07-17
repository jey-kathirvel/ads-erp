from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.booking.models import Booking, BookingRoom, Room, RoomType
from app.booking.service import BookingService
from app.models.base import Base


def test_expired_online_hold_is_cancelled_and_room_is_released():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    now = datetime(2026, 7, 17, 12, 0)
    room_type = RoomType(name="AC Double", total_rooms=1, room_rate=1899)
    db.add(room_type)
    db.flush()
    room = Room(room_number="101", room_type_id=room_type.id)
    db.add(room)
    db.flush()
    booking = Booking(
        booking_no="ON-EXPIRED", guest_name="Online Guest", mobile="9092977055",
        email="guest@example.com", check_in_at=now + timedelta(days=1),
        check_out_at=now + timedelta(days=2), number_of_days=1,
        room_type_id=room_type.id, number_of_rooms=1, room_rate=1899,
        subtotal_amount=1899, gst_percent=5, gst_amount=94.95,
        total_amount=1993.95, advance_amount=0, payment_mode="RAZORPAY",
        booking_source="ONLINE", payment_expires_at=now - timedelta(seconds=1),
        provider_order_id="order_expired", status="RESERVED",
    )
    db.add(booking)
    db.flush()
    booking_room = BookingRoom(booking_id=booking.id, room_id=room.id, status="ACTIVE")
    db.add(booking_room)
    db.commit()

    assert BookingService.expire_online_payment_holds(db, now=now) == 1
    db.refresh(booking)
    db.refresh(booking_room)
    assert booking.status == "CANCELLED"
    assert BookingService.ONLINE_PAYMENT_EXPIRED_REASON in booking.notes
    assert booking_room.status == "CANCELLED"
    assert booking_room.cancelled_at == now
    assert booking_room.cancellation_reason == BookingService.ONLINE_PAYMENT_EXPIRED_REASON
    db.close()
