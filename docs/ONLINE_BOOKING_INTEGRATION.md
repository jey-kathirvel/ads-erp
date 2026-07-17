# Online booking integration

## Shared data model

`online-ars` and ADS ERP use the same `room_types`, `rooms`, `bookings`, `booking_rooms` and `booking_payments` tables. `booking_source` distinguishes `ERP` and `ONLINE` records.

## Availability rules

Overlapping bookings block a room when the booking status is `RESERVED`, `CONFIRMED` or `CHECKED_IN` and the room allocation is `ACTIVE`. An online `RESERVED` record blocks inventory only until `payment_expires_at`.

## Payment lifecycle

```text
Online Razorpay order created
  → booking RESERVED
  → room held for 10 minutes
  → ERP displays guest mobile and live countdown

Payment captured and verified
  → booking CONFIRMED
  → advance equals GST-inclusive total
  → booking payment stored as CAPTURED

Payment not completed before expiry
  → booking CANCELLED
  → dashboard payment status PAYMENT EXPIRED
  → reason Online payment window expired
  → room allocation CANCELLED and immediately released
```

The dashboard refreshes when its countdown reaches zero. The server performs the authoritative expiry transition in one database transaction.

## Payment differences

- Public online bookings require complete payment.
- Staff-created ERP bookings may accept partial or complete payment.
- Both sources appear in the booking report source filter.

## Time handling

Online payment expiry is stored and compared as naive UTC. Hotel check-in/check-out presentation uses India time conventions. Do not compare a UTC payment expiry directly with an IST-naive value.
