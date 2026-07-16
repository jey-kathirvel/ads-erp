from datetime import datetime

from app.booking.service import BookingService


def test_checkout_uses_24_hour_rule():
    check_in = datetime(2026, 7, 15, 10, 30)
    assert BookingService.calculate_check_out(check_in, 2) == datetime(2026, 7, 17, 10, 30)
