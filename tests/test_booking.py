from datetime import datetime

from app.booking.service import BookingService


def test_checkout_uses_24_hour_rule():
    check_in = datetime(2026, 7, 15, 10, 30)
    assert BookingService.calculate_check_out(check_in, 2) == datetime(2026, 7, 17, 10, 30)


def test_price_includes_five_percent_gst():
    subtotal, gst, total = BookingService.calculate_price(1899, 1, 2, 5)
    assert str(subtotal) == "3798.00"
    assert str(gst) == "189.90"
    assert str(total) == "3987.90"
