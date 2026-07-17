from app.booking.models import BookingRoom
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Form
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import login_required
from app.booking.models import Booking
from app.booking.models import BookingPayment
from app.booking.models import Room
from app.booking.models import RoomType
from app.booking.service import BookingService
from app.booking.email_service import BookingEmail, send_booking_confirmation
from app.config.database import get_db
from app.config.settings import settings
import razorpay
from razorpay.errors import SignatureVerificationError



ACTIVE_BOOKING_STATUSES = (
    "RESERVED",
    "CONFIRMED",
    "CHECKED_IN",
)


router = APIRouter(
    dependencies=[Depends(login_required)]
)


def india_now() -> datetime:
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).replace(
        tzinfo=None
    )


templates = Jinja2Templates(
    directory="app/templates"
)


def razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Razorpay is not configured")
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@router.post("/booking/api/payment/order")
async def create_booking_payment_order(
    room_type_id: int = Form(...),
    number_of_days: int = Form(...),
    number_of_rooms: int = Form(...),
    advance_amount: float = Form(...),
    db: Session = Depends(get_db),
):
    if number_of_days < 1 or number_of_rooms < 1:
        raise HTTPException(status_code=400, detail="Select a valid stay and room")

    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id, RoomType.is_active.is_(True)
    ).first()
    if room_type is None:
        raise HTTPException(status_code=404, detail="Room type not found")

    subtotal_amount, gst_amount, total_amount = BookingService.calculate_price(
        room_type.room_rate, number_of_rooms, number_of_days, settings.BOOKING_GST_PERCENT
    )
    total_amount = float(total_amount)
    if advance_amount <= 0 or advance_amount > total_amount:
        raise HTTPException(
            status_code=400,
            detail="Payment must be greater than zero and cannot exceed the booking total",
        )

    amount_paise = round(advance_amount * 100)
    try:
        order = razorpay_client().order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": "booking-" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:31],
            "notes": {"purpose": "hotel_booking"},
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to start Razorpay payment") from exc

    return {
        "key_id": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "total_amount": total_amount,
    }


@router.get(
    "/booking",
    response_class=HTMLResponse,
)
async def booking_dashboard(
    request: Request,
    user=Depends(login_required),
    db: Session = Depends(get_db),
):

    now = india_now()
    utc_now = datetime.utcnow()
    BookingService.expire_online_payment_holds(
        db=db,
        now=utc_now,
    )

    total_rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .count()
    )

    room_types = (
        db.query(RoomType)
        .filter(RoomType.is_active.is_(True))
        .order_by(RoomType.id)
        .all()
    )

    occupied_now = (
        db.query(Room.id)
        .join(
            Room.booking_rooms
        )
        .join(
            Booking,
        )
        .filter(
            Room.is_active.is_(True),
            Booking.status.in_(
                (
                    "RESERVED",
                    "CONFIRMED",
                    "CHECKED_IN",
                )
            ),
            Booking.check_in_at <= now,
            Booking.check_out_at > now,
        )
        .distinct()
        .count()
    )

    available_now = max(
        total_rooms - occupied_now,
        0,
    )

    room_type_summary = []

    for room_type in room_types:

        type_total = (
            db.query(Room)
            .filter(
                Room.room_type_id == room_type.id,
                Room.is_active.is_(True),
            )
            .count()
        )

        type_available = (
            BookingService.get_available_count(
                db=db,
                room_type_id=room_type.id,
                check_in_at=now,
                check_out_at=now.replace(
                    microsecond=0
                )
                + __import__("datetime").timedelta(
                    seconds=1
                ),
            )
        )

        room_type_summary.append(
            {
                "id": room_type.id,
                "name": room_type.name,
                "total": type_total,
                "available": type_available,
                "occupied": max(
                    type_total - type_available,
                    0,
                ),
            }
        )

    active_bookings = (
        db.query(Booking)
        .filter(
            Booking.status.in_(
                (
                    "RESERVED",
                    "CONFIRMED",
                    "CHECKED_IN",
                )
            ),
            Booking.check_out_at > now,
        )
        .order_by(
            Booking.created_at.desc(),
            Booking.id.desc(),
        )
        .limit(10)
        .all()
    )

    online_payment_requests = []
    online_bookings = (
        db.query(Booking)
        .filter(Booking.booking_source == "ONLINE")
        .order_by(Booking.created_at.desc(), Booking.id.desc())
        .limit(20)
        .all()
    )
    for booking in online_bookings:
        remaining_seconds = 0
        if booking.status == "RESERVED" and booking.payment_expires_at:
            remaining_seconds = max(
                int((booking.payment_expires_at - utc_now).total_seconds()),
                0,
            )
            payment_status = "AWAITING PAYMENT"
            payment_badge = "warning"
        elif booking.status in ("CONFIRMED", "CHECKED_IN", "CHECKED_OUT"):
            payment_status = "PAYMENT CAPTURED"
            payment_badge = "success"
        elif booking.status == "CANCELLED" and (
            BookingService.ONLINE_PAYMENT_EXPIRED_REASON in (booking.notes or "")
        ):
            payment_status = "PAYMENT EXPIRED"
            payment_badge = "danger"
        else:
            payment_status = booking.status
            payment_badge = "secondary"
        online_payment_requests.append(
            {
                "booking": booking,
                "remaining_seconds": remaining_seconds,
                "payment_status": payment_status,
                "payment_badge": payment_badge,
                "cancellation_reason": (
                    BookingService.ONLINE_PAYMENT_EXPIRED_REASON
                    if payment_status == "PAYMENT EXPIRED"
                    else ""
                ),
            }
        )

    # -------------------------------------
    # Checkout alerts: next 2 hours
    # -------------------------------------

    checkout_alert_until = (
        now
        + __import__("datetime").timedelta(
            hours=2
        )
    )

    checkout_alert_bookings = (
        db.query(Booking)
        .filter(
            Booking.status.in_(
                ACTIVE_BOOKING_STATUSES
            ),
            Booking.check_out_at >= now,
            Booking.check_out_at
            <= checkout_alert_until,
        )
        .order_by(
            Booking.check_out_at.asc()
        )
        .all()
    )

    checkout_alerts = []

    for booking in checkout_alert_bookings:

        room_rows = (
            db.query(Room.room_number)
            .join(
                BookingRoom,
                BookingRoom.room_id
                == Room.id,
            )
            .filter(
                BookingRoom.booking_id
                == booking.id
            )
            .order_by(
                Room.room_number.asc()
            )
            .all()
        )

        room_numbers = [
            str(row[0])
            for row in room_rows
        ]

        remaining_seconds = max(
            int(
                (
                    booking.check_out_at
                    - now
                ).total_seconds()
            ),
            0,
        )

        remaining_minutes = (
            remaining_seconds // 60
        )

        remaining_hours = (
            remaining_minutes // 60
        )

        remaining_minute_part = (
            remaining_minutes % 60
        )

        if remaining_minutes <= 30:
            severity = "danger"
            severity_label = "Urgent"

        elif remaining_minutes <= 60:
            severity = "warning"
            severity_label = "Due Soon"

        else:
            severity = "info"
            severity_label = "Upcoming"

        checkout_alerts.append(
            {
                "booking_id": booking.id,
                "booking_no": booking.booking_no,
                "guest_name": booking.guest_name,
                "mobile": booking.mobile,
                "status": booking.status,
                "room_numbers": room_numbers,
                "check_out_at": booking.check_out_at,
                "remaining_minutes": remaining_minutes,
                "remaining_text": (
                    f"{remaining_hours}h "
                    f"{remaining_minute_part}m"
                ),
                "severity": severity,
                "severity_label": severity_label,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="booking/dashboard.html",
        context={
            "user": user,
            "now": now,
            "total_rooms": total_rooms,
            "occupied_now": occupied_now,
            "available_now": available_now,
            "room_type_summary": room_type_summary,
            "active_bookings": active_bookings,
            "online_payment_requests": online_payment_requests,
            "checkout_alerts": checkout_alerts,
            "checkout_alert_until": checkout_alert_until,
        },
    )


@router.get(
    "/booking/new",
    response_class=HTMLResponse,
)
async def new_booking_form(
    request: Request,
    user=Depends(login_required),
    db: Session = Depends(get_db),
):

    room_types = (
        db.query(RoomType)
        .filter(RoomType.is_active.is_(True))
        .order_by(RoomType.id)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="booking/new.html",
        context={
            "user": user,
            "room_types": room_types,
        },
    )



@router.get(
    "/booking/api/availability"
)
async def booking_availability(
    room_type_id: int = Query(..., ge=1),
    check_in_at: datetime = Query(...),
    number_of_days: int = Query(
        1,
        ge=1,
        le=365,
    ),
    check_out_at: datetime | None = Query(
        None,
    ),
    exclude_booking_id: int | None = Query(
        None,
        ge=1,
    ),
    db: Session = Depends(get_db),
):

    room_type = (
        db.query(RoomType)
        .filter(
            RoomType.id == room_type_id,
            RoomType.is_active.is_(True),
        )
        .first()
    )

    if room_type is None:
        raise HTTPException(
            status_code=404,
            detail="Room type not found",
        )

    effective_check_out_at = check_out_at

    if effective_check_out_at is None:
        effective_check_out_at = (
            BookingService.calculate_check_out(
                check_in_at=check_in_at,
                number_of_days=number_of_days,
            )
        )

    if effective_check_out_at <= check_in_at:
        raise HTTPException(
            status_code=400,
            detail="Check-out must be after check-in",
        )

    available_rooms = (
        BookingService.get_available_rooms(
            db=db,
            room_type_id=room_type_id,
            check_in_at=check_in_at,
            check_out_at=effective_check_out_at,
            exclude_booking_id=exclude_booking_id,
        )
    )

    return {
        "room_type_id": room_type.id,
        "room_type_name": room_type.name,
        "check_in_at": check_in_at.isoformat(),
        "check_out_at": effective_check_out_at.isoformat(),
        "checkout_source": (
            "MANUAL"
            if check_out_at is not None
            else "AUTO"
        ),
        "number_of_days": number_of_days,
        "exclude_booking_id": exclude_booking_id,
        "available_count": len(
            available_rooms
        ),
        "available_rooms": [
            room.room_number
            for room in available_rooms
        ],
    }

@router.post(
    "/booking",
    name="save_booking",
)
async def save_booking(
    request: Request,
    guest_name: str = Form(...),
    mobile: str = Form(...),
    email: str = Form(""),
    selected_room_ids: str = Form(...),
    room_type_id: int = Form(...),
    check_in_date: str = Form(...),
    check_in_time: str = Form(...),
    number_of_days: int = Form(...),
    check_out_at: str = Form(""),
    number_of_rooms: int = Form(...),
    advance_amount: float = Form(0),
    payment_mode: str = Form(""),
    notes: str = Form(""),
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    guest_name = guest_name.strip()
    mobile = mobile.strip()

    if len(guest_name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Guest name is required",
        )

    if (
        len(mobile) != 10
        or not mobile.isdigit()
    ):
        raise HTTPException(
            status_code=400,
            detail="Valid 10-digit mobile number is required",
        )

    selected_room_numbers = [
        value.strip()
        for value in selected_room_ids.split(",")
        if value.strip()
    ]

    if not selected_room_numbers:
        raise HTTPException(
            status_code=400,
            detail="At least one room must be selected",
        )

    if len(selected_room_numbers) != len(
        set(selected_room_numbers)
    ):
        raise HTTPException(
            status_code=400,
            detail="Duplicate room selection is not allowed",
        )

    check_in_at = datetime.fromisoformat(
        f"{check_in_date}T{check_in_time}"
    )

    manual_check_out_value = (
        check_out_at.strip()
        if check_out_at
        else ""
    )

    if manual_check_out_value:
        try:
            effective_check_out_at = (
                datetime.fromisoformat(
                    manual_check_out_value
                )
            )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid check-out date or time",
            )

        checkout_source = "MANUAL"

    else:
        effective_check_out_at = (
            BookingService.calculate_check_out(
                check_in_at=check_in_at,
                number_of_days=number_of_days,
            )
        )

        checkout_source = "AUTO"

    if effective_check_out_at <= check_in_at:
        raise HTTPException(
            status_code=400,
            detail="Check-out must be after check-in",
        )

    if number_of_days < 1:
        raise HTTPException(
            status_code=400,
            detail="Number of days must be at least 1",
        )

    if number_of_rooms < 1:
        raise HTTPException(
            status_code=400,
            detail="Number of rooms must be at least 1",
        )

    room_type = (
        db.query(RoomType)
        .filter(
            RoomType.id == room_type_id,
            RoomType.is_active.is_(True),
        )
        .first()
    )

    if not room_type:
        raise HTTPException(
            status_code=404,
            detail="Room type not found",
        )

    available_rooms = (
        BookingService.get_available_rooms(
            db=db,
            room_type_id=room_type_id,
            check_in_at=check_in_at,
            check_out_at=effective_check_out_at,
        )
    )

    if len(available_rooms) < number_of_rooms:
        raise HTTPException(
            status_code=409,
            detail=(
                "Requested rooms are no longer available"
            ),
        )

    available_room_map = {
        str(room.room_number): room
        for room in available_rooms
    }

    unavailable_selected_rooms = [
        room_number
        for room_number in selected_room_numbers
        if room_number not in available_room_map
    ]

    if unavailable_selected_rooms:
        raise HTTPException(
            status_code=409,
            detail=(
                "One or more selected rooms are no longer available"
            ),
        )

    selected_rooms = [
        available_room_map[room_number]
        for room_number in selected_room_numbers
    ]

    number_of_rooms = len(selected_rooms)

    subtotal_amount, gst_amount, total_amount = BookingService.calculate_price(
        room_type.room_rate, number_of_rooms, number_of_days, settings.BOOKING_GST_PERCENT
    )
    total_amount = float(total_amount)
    if advance_amount <= 0 or advance_amount > total_amount:
        raise HTTPException(status_code=400, detail="Invalid payment amount")

    client = razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        order = client.order.fetch(razorpay_order_id)
        payment = client.payment.fetch(razorpay_payment_id)
    except SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Payment signature verification failed") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to verify Razorpay payment") from exc

    expected_paise = round(advance_amount * 100)
    if (
        order.get("amount") != expected_paise
        or payment.get("amount") != expected_paise
        or payment.get("order_id") != razorpay_order_id
        or payment.get("status") != "captured"
        or order.get("currency") != "INR"
    ):
        raise HTTPException(status_code=400, detail="Payment is not captured or amount does not match")

    existing_payment = db.query(BookingPayment).filter(
        BookingPayment.provider_payment_id == razorpay_payment_id
    ).first()
    if existing_payment:
        return RedirectResponse(url=f"/booking/{existing_payment.booking_id}", status_code=303)

    booking_no = (
        "BK-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    booking = Booking(
        booking_no=booking_no,
        guest_name=guest_name,
        mobile=mobile,
        email=email.strip().lower() or None,
        room_type_id=room_type_id,
        check_in_at=check_in_at,
        check_out_at=effective_check_out_at,
        number_of_days=number_of_days,
        number_of_rooms=number_of_rooms,
        room_rate=room_type.room_rate,
        subtotal_amount=subtotal_amount,
        gst_percent=settings.BOOKING_GST_PERCENT,
        gst_amount=gst_amount,
        total_amount=total_amount,
        advance_amount=advance_amount,
        payment_mode="RAZORPAY",
        booking_source="ERP",
        notes=notes.strip() or None,
        status="CONFIRMED",
    )

    db.add(booking)
    db.flush()

    for room in selected_rooms:
        db.add(
            BookingRoom(
                booking_id=booking.id,
                room_id=room.id,
            )
        )

    db.add(BookingPayment(
        booking_id=booking.id,
        provider="RAZORPAY",
        provider_order_id=razorpay_order_id,
        provider_payment_id=razorpay_payment_id,
        amount=advance_amount,
        currency="INR",
        status="CAPTURED",
    ))

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    send_booking_confirmation(BookingEmail(
        recipient=booking.email or "", guest_name=booking.guest_name,
        booking_no=booking.booking_no, room_type=room_type.name,
        check_in_at=booking.check_in_at, check_out_at=booking.check_out_at,
        number_of_rooms=booking.number_of_rooms, number_of_days=booking.number_of_days,
        subtotal_amount=booking.subtotal_amount, gst_amount=booking.gst_amount,
        total_amount=booking.total_amount, paid_amount=booking.advance_amount,
        balance_amount=float(booking.total_amount)-float(booking.advance_amount),
        payment_mode="Razorpay", payment_id=razorpay_payment_id,
    ))

    return RedirectResponse(
        url="/booking",
        status_code=303,
    )


@router.get(
    "/booking/api/same-day",
)
async def same_day_bookings(
    booking_date: date = Query(...),
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    day_start = datetime.combine(
        booking_date,
        datetime.min.time(),
    )

    day_end = (
        day_start
        + timedelta(days=1)
    )

    bookings = (
        db.query(Booking)
        .filter(
            Booking.status != "CANCELLED",
            Booking.check_in_at < day_end,
            Booking.check_out_at > day_start,
        )
        .order_by(
            Booking.created_at.desc(),
            Booking.id.desc(),
        )
        .all()
    )

    result = []

    for booking in bookings:
        room_numbers = sorted(
            [
                link.room.room_number
                for link in booking.booking_rooms
                if link.room is not None
            ],
            key=lambda value: (
                0,
                int(value),
            )
            if str(value).isdigit()
            else (
                1,
                str(value),
            ),
        )

        result.append(
            {
                "id": booking.id,
                "booking_no": booking.booking_no,
                "guest_name": booking.guest_name,
                "mobile": booking.mobile,
                "room_type": (
                    booking.room_type.name
                    if booking.room_type
                    else ""
                ),
                "room_numbers": room_numbers,
                "check_in_at": (
                    booking.check_in_at.isoformat()
                ),
                "check_out_at": (
                    booking.check_out_at.isoformat()
                ),
                "status": booking.status,
                "view_url": (
                    f"/booking/{booking.id}/view"
                ),
                "edit_url": (
                    f"/booking/{booking.id}/edit"
                ),
                "cancel_url": (
                    f"/booking/{booking.id}/cancel"
                ),
            }
        )

    return {
        "booking_date": booking_date.isoformat(),
        "count": len(result),
        "bookings": result,
    }


@router.get(
    "/booking/{booking_id}/view",
    response_class=HTMLResponse,
)
async def view_booking(
    request: Request,
    booking_id: int,
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="booking/view.html",
        context={
            "user": user,
            "booking": booking,
        },
    )



@router.post(
    "/booking/{booking_id}/edit",
    name="update_booking",
)
async def update_booking(
    booking_id: int,
    guest_name: str = Form(...),
    mobile: str = Form(...),
    room_type_id: int = Form(...),
    check_in_date: str = Form(...),
    check_in_time: str = Form(...),
    number_of_days: int = Form(...),
    check_out_at: str = Form(""),
    number_of_rooms: int = Form(...),
    selected_rooms: list[str] = Form(...),
    advance_amount: float = Form(0),
    payment_mode: str = Form(""),
    notes: str = Form(""),
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=409,
            detail="Cancelled booking cannot be edited",
        )

    guest_name = guest_name.strip()
    mobile = mobile.strip()

    if not guest_name:
        raise HTTPException(
            status_code=400,
            detail="Guest name is required",
        )

    if not mobile:
        raise HTTPException(
            status_code=400,
            detail="Mobile number is required",
        )

    if number_of_days < 1:
        raise HTTPException(
            status_code=400,
            detail="Number of days must be at least 1",
        )

    if number_of_rooms < 1:
        raise HTTPException(
            status_code=400,
            detail="Number of rooms must be at least 1",
        )

    selected_room_numbers = [
        str(value).strip()
        for value in selected_rooms
        if str(value).strip()
    ]

    if len(selected_room_numbers) != number_of_rooms:
        raise HTTPException(
            status_code=400,
            detail=(
                "Selected room count does not match "
                "number of rooms"
            ),
        )

    if len(selected_room_numbers) != len(
        set(selected_room_numbers)
    ):
        raise HTTPException(
            status_code=400,
            detail="Duplicate room selection is not allowed",
        )

    try:
        check_in_at = datetime.fromisoformat(
            f"{check_in_date}T{check_in_time}"
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid check-in date or time",
        )

    manual_check_out_value = (
        check_out_at.strip()
        if check_out_at
        else ""
    )

    if manual_check_out_value:
        try:
            effective_check_out_at = (
                datetime.fromisoformat(
                    manual_check_out_value
                )
            )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid check-out date or time",
            )

        checkout_source = "MANUAL"

    else:
        effective_check_out_at = (
            BookingService.calculate_check_out(
                check_in_at=check_in_at,
                number_of_days=number_of_days,
            )
        )

        checkout_source = "AUTO"

    if effective_check_out_at <= check_in_at:
        raise HTTPException(
            status_code=400,
            detail="Check-out must be after check-in",
        )

    room_type = (
        db.query(RoomType)
        .filter(
            RoomType.id == room_type_id,
            RoomType.is_active.is_(True),
        )
        .first()
    )

    if room_type is None:
        raise HTTPException(
            status_code=404,
            detail="Room type not found",
        )

    available_rooms = (
        BookingService.get_available_rooms(
            db=db,
            room_type_id=room_type_id,
            check_in_at=check_in_at,
            check_out_at=effective_check_out_at,
            exclude_booking_id=booking.id,
        )
    )

    available_room_map = {
        str(room.room_number): room
        for room in available_rooms
    }

    unavailable_selected_rooms = [
        room_number
        for room_number in selected_room_numbers
        if room_number not in available_room_map
    ]

    if unavailable_selected_rooms:
        raise HTTPException(
            status_code=409,
            detail=(
                "Selected room(s) are no longer available: "
                + ", ".join(
                    unavailable_selected_rooms
                )
            ),
        )

    selected_room_objects = [
        available_room_map[room_number]
        for room_number in selected_room_numbers
    ]

    try:
        booking.guest_name = guest_name
        booking.mobile = mobile
        booking.room_type_id = room_type_id
        booking.check_in_at = check_in_at
        booking.check_out_at = effective_check_out_at
        booking.number_of_days = number_of_days
        booking.number_of_rooms = number_of_rooms
        booking.room_rate = room_type.room_rate
        subtotal, gst, total = BookingService.calculate_price(
            room_type.room_rate, number_of_rooms, number_of_days, settings.BOOKING_GST_PERCENT
        )
        booking.subtotal_amount = subtotal
        booking.gst_percent = settings.BOOKING_GST_PERCENT
        booking.gst_amount = gst
        booking.total_amount = total
        booking.advance_amount = advance_amount
        booking.payment_mode = (
            payment_mode.strip() or None
        )
        booking.notes = (
            notes.strip() or None
        )

        active_assignments = (
            db.query(BookingRoom)
            .filter(
                BookingRoom.booking_id == booking.id,
                BookingRoom.status == "ACTIVE",
            )
            .all()
        )

        active_assignment_by_room_id = {
            assignment.room_id: assignment
            for assignment in active_assignments
        }

        selected_room_ids = {
            room.id
            for room in selected_room_objects
        }

        current_active_room_ids = set(
            active_assignment_by_room_id
        )

        removed_active_room_ids = (
            current_active_room_ids
            - selected_room_ids
        )

        if removed_active_room_ids:
            removed_room_numbers = [
                str(assignment.room.room_number)
                for assignment in active_assignments
                if assignment.room_id
                in removed_active_room_ids
            ]

            raise HTTPException(
                status_code=409,
                detail=(
                    "Room removal is not allowed in Edit Booking. "
                    "Use Cancel Selected Rooms for: "
                    + ", ".join(
                        sorted(
                            removed_room_numbers
                        )
                    )
                ),
            )

        new_room_ids = (
            selected_room_ids
            - current_active_room_ids
        )

        for room in selected_room_objects:
            if room.id not in new_room_ids:
                continue

            db.add(
                BookingRoom(
                    booking_id=booking.id,
                    room_id=room.id,
                    status="ACTIVE",
                )
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url=f"/booking/{booking.id}/view",
        status_code=303,
    )


@router.get(
    "/booking/{booking_id}/edit",
    response_class=HTMLResponse,
)
async def edit_booking_form(
    request: Request,
    booking_id: int,
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    room_types = (
        db.query(RoomType)
        .filter(
            RoomType.is_active.is_(True)
        )
        .order_by(RoomType.id)
        .all()
    )

    selected_room_numbers = [
        link.room.room_number
        for link in booking.booking_rooms
        if (
            link.room is not None
            and link.status == "ACTIVE"
        )
    ]

    return templates.TemplateResponse(
        request=request,
        name="booking/edit.html",
        context={
            "user": user,
            "booking": booking,
            "room_types": room_types,
            "selected_room_numbers": (
                selected_room_numbers
            ),
        },
    )


@router.post(
    "/booking/{booking_id}/cancel-rooms",
    name="cancel_booking_rooms",
)
async def cancel_booking_rooms(
    booking_id: int,
    assignment_ids: list[int] = Form(...),
    cancellation_reason: str = Form(...),
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Cancelled booking cannot have "
                "partial room cancellation"
            ),
        )

    normalized_assignment_ids = sorted(
        set(
            int(value)
            for value in assignment_ids
        )
    )

    if not normalized_assignment_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Select at least one room "
                "to cancel"
            ),
        )

    reason = cancellation_reason.strip()

    if not reason:
        raise HTTPException(
            status_code=400,
            detail="Cancellation reason is required",
        )

    active_assignments = (
        db.query(BookingRoom)
        .filter(
            BookingRoom.booking_id == booking.id,
            BookingRoom.status == "ACTIVE",
        )
        .order_by(
            BookingRoom.id.asc()
        )
        .all()
    )

    if not active_assignments:
        raise HTTPException(
            status_code=409,
            detail=(
                "Booking has no active room "
                "assignments"
            ),
        )

    active_assignment_map = {
        assignment.id: assignment
        for assignment in active_assignments
    }

    invalid_assignment_ids = [
        assignment_id
        for assignment_id
        in normalized_assignment_ids
        if assignment_id
        not in active_assignment_map
    ]

    if invalid_assignment_ids:
        raise HTTPException(
            status_code=409,
            detail=(
                "Selected room assignment(s) "
                "are invalid, already cancelled, "
                "or do not belong to this booking: "
                + ", ".join(
                    str(value)
                    for value
                    in invalid_assignment_ids
                )
            ),
        )

    if len(normalized_assignment_ids) >= len(
        active_assignments
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Partial cancellation cannot cancel "
                "all active rooms. Use whole booking "
                "cancellation instead."
            ),
        )

    assignments_to_cancel = [
        active_assignment_map[
            assignment_id
        ]
        for assignment_id
        in normalized_assignment_ids
    ]

    cancellation_time = india_now()

    try:
        for assignment in assignments_to_cancel:
            assignment.status = "CANCELLED"
            assignment.cancelled_at = (
                cancellation_time
            )
            assignment.cancellation_reason = (
                reason
            )

        remaining_active_count = (
            len(active_assignments)
            - len(assignments_to_cancel)
        )

        booking.number_of_rooms = (
            remaining_active_count
        )

        subtotal, gst, total = BookingService.calculate_price(
            booking.room_rate, remaining_active_count, booking.number_of_days, booking.gst_percent
        )
        booking.subtotal_amount = subtotal
        booking.gst_amount = gst
        booking.total_amount = total

        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url=f"/booking/{booking.id}/view",
        status_code=303,
    )


@router.post(
    "/booking/{booking_id}/cancel",
    name="cancel_booking",
)
async def cancel_booking(
    booking_id: int,
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.status == "CANCELLED":
        return RedirectResponse(
            url="/booking",
            status_code=303,
        )

    booking.status = "CANCELLED"

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url="/booking",
        status_code=303,
    )

