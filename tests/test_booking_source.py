from app.booking.models import Booking


def test_booking_source_column_defaults_to_erp():
    assert Booking.__table__.c.booking_source.default.arg == "ERP"
