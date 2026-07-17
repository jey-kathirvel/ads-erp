# Hotel booking acceptance testing

## Automated

```bash
python -m pytest -q tests/test_booking.py tests/test_booking_source.py tests/test_online_hold_expiry.py
```

Run the full suite with development dependencies and Playwright installed.

## Staff-to-online synchronization

1. Create a confirmed ERP booking.
2. Search the same room type and overlapping period online.
3. Confirm the allocated room is unavailable online.

## Online-to-staff synchronization

1. Begin a Razorpay test payment online.
2. Open ERP Booking Dashboard.
3. Confirm `AWAITING PAYMENT`, guest mobile number and a decreasing ten-minute countdown.
4. Confirm staff cannot allocate the held room.

## Successful payment

1. Complete Razorpay test checkout.
2. Confirm booking changes to `CONFIRMED`.
3. Confirm payment shows `PAYMENT CAPTURED`.
4. Confirm the payment amount equals the complete GST-inclusive total.
5. Confirm source is `ONLINE` in the booking report.

## Expired payment

1. Start checkout and do not complete it.
2. Allow the countdown to reach zero.
3. Confirm dashboard refreshes to `CANCELLED / PAYMENT EXPIRED`.
4. Confirm guest mobile and cancellation reason remain visible.
5. Confirm the room becomes available to staff and online users.
