from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from fastapi.templating import Jinja2Templates

from app.auth.dependencies import login_required
from app.booking.models import Booking, Room
from app.config.database import get_db
from app.hotel_operations.constants import (
    ROOM_STATUSES,
    STAFF_DEPARTMENTS,
    TASK_PRIORITIES,
    TASK_STATUSES,
    TASK_TYPES,
)
from app.hotel_operations.models import (
    HotelInventoryItem,
    HotelInventoryTransaction,
    HotelLaundryBatch,
    HotelLaundryBatchItem,
    HotelRoomStatus,
    HotelStaff,
    HousekeepingTask,
)
from app.hotel_operations.service import HotelOperationsService

templates = Jinja2Templates(directory="app/templates")


router = APIRouter(
    prefix="/hotel-operations",
    dependencies=[Depends(login_required)],
)


def current_user_name(request: Request) -> str | None:
    user = request.session.get("user", {})

    return (
        user.get("name")
        or user.get("full_name")
        or user.get("username")
        or user.get("email")
    )


def parse_inventory_quantity(
    value: str,
    field_name: str,
    *,
    allow_zero: bool = False,
) -> Decimal:
    try:
        quantity = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid number.",
        )

    if allow_zero:
        if quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} cannot be negative.",
            )
    elif quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be greater than zero.",
        )

    return quantity.quantize(Decimal("0.01"))


def normalize_inventory_transaction_type(
    transaction_type: str,
) -> str:
    normalized = transaction_type.strip().upper()

    allowed_types = {
        "STOCK_IN",
        "STOCK_OUT",
        "LINEN_ISSUE",
        "LINEN_RETURN",
        "ADJUSTMENT_IN",
        "ADJUSTMENT_OUT",
    }

    if normalized not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid inventory transaction type.",
        )

    return normalized


def inventory_transaction_direction(
    transaction_type: str,
) -> int:
    inward_types = {
        "STOCK_IN",
        "LINEN_RETURN",
        "ADJUSTMENT_IN",
    }

    return 1 if transaction_type in inward_types else -1


LAUNDRY_BATCH_STATUSES = (
    "COLLECTED",
    "SENT_TO_LAUNDRY",
    "IN_PROCESS",
    "PARTIALLY_RETURNED",
    "COMPLETED",
    "CANCELLED",
)

LAUNDRY_SOURCE_TYPES = (
    "ROOM",
    "HOUSEKEEPING",
    "GENERAL",
)


def parse_optional_datetime(
    value: str | None,
    field_name: str,
) -> datetime | None:
    normalized = (value or "").strip()

    if not normalized:
        return None

    try:
        return datetime.fromisoformat(normalized)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} must be a valid date and time."
            ),
        ) from error


def normalize_laundry_status(
    value: str,
) -> str:
    normalized = value.strip().upper()

    if normalized not in LAUNDRY_BATCH_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid laundry batch status.",
        )

    return normalized


def normalize_laundry_source_type(
    value: str,
) -> str:
    normalized = value.strip().upper()

    if normalized not in LAUNDRY_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid laundry source type.",
        )

    return normalized


def generate_laundry_batch_no(
    db: Session,
) -> str:
    date_prefix = datetime.utcnow().strftime(
        "LDR-%Y%m%d"
    )

    count_for_day = (
        db.query(
            func.count(HotelLaundryBatch.id)
        )
        .filter(
            HotelLaundryBatch.batch_no.like(
                f"{date_prefix}-%"
            )
        )
        .scalar()
        or 0
    )

    sequence = int(count_for_day) + 1

    while True:
        batch_no = (
            f"{date_prefix}-{sequence:03d}"
        )

        exists = (
            db.query(HotelLaundryBatch.id)
            .filter(
                HotelLaundryBatch.batch_no
                == batch_no
            )
            .first()
        )

        if not exists:
            return batch_no

        sequence += 1


def apply_laundry_inventory_movement(
    *,
    db: Session,
    inventory_item: HotelInventoryItem,
    transaction_type: str,
    quantity: Decimal,
    reference_no: str,
    remarks: str,
) -> Decimal:
    current_balance = Decimal(
        inventory_item.current_stock
    ).quantize(
        Decimal("0.01")
    )

    normalized_quantity = Decimal(
        quantity
    ).quantize(
        Decimal("0.01")
    )

    if transaction_type in {
        "LINEN_ISSUE",
        "STOCK_OUT",
        "ADJUSTMENT_OUT",
    }:
        new_balance = (
            current_balance
            - normalized_quantity
        )
    elif transaction_type in {
        "LINEN_RETURN",
        "STOCK_IN",
        "ADJUSTMENT_IN",
    }:
        new_balance = (
            current_balance
            + normalized_quantity
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported laundry inventory "
                "transaction type."
            ),
        )

    if new_balance < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock for "
                f"{inventory_item.item_name}. "
                f"Available: "
                f"{current_balance} "
                f"{inventory_item.unit}."
            ),
        )

    new_balance = new_balance.quantize(
        Decimal("0.01")
    )

    inventory_item.current_stock = (
        new_balance
    )

    transaction = HotelInventoryTransaction(
        inventory_item_id=inventory_item.id,
        transaction_type=transaction_type,
        quantity=normalized_quantity,
        balance_after=new_balance,
        reference_no=reference_no,
        remarks=remarks,
    )

    db.add(transaction)

    return new_balance


@router.get("")
async def hotel_operations_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    room_status_counts: dict[str, int] = {}

    for room in rooms:
        room_status = HotelOperationsService.ensure_room_status(
            db=db,
            room_id=room.id,
        )
        room_status_counts[room_status.status] = (
            room_status_counts.get(room_status.status, 0) + 1
        )

    active_task_statuses = [
        "PENDING",
        "ASSIGNED",
        "IN_PROGRESS",
    ]

    recent_tasks = (
        db.query(HousekeepingTask)
        .order_by(HousekeepingTask.created_at.desc())
        .limit(8)
        .all()
    )

    active_tasks = (
        db.query(HousekeepingTask)
        .filter(HousekeepingTask.status.in_(active_task_statuses))
        .count()
    )

    active_staff = (
        db.query(HotelStaff)
        .filter(HotelStaff.is_active.is_(True))
        .count()
    )

    ready_rooms = sum(
        room_status_counts.get(status, 0)
        for status in [
            "VACANT_CLEAN",
            "READY_FOR_CHECKIN",
        ]
    )

    db.commit()

    return templates.TemplateResponse(
        "hotel_operations/dashboard.html",
        {
            "request": request,
            "total_rooms": len(rooms),
            "ready_rooms": ready_rooms,
            "active_tasks": active_tasks,
            "active_staff": active_staff,
            "room_status_counts": room_status_counts,
            "recent_tasks": recent_tasks,
        },
    )


@router.get("/rooms")
async def hotel_operations_room_board(
    request: Request,
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    room_items = []

    for room in rooms:
        room_status = HotelOperationsService.ensure_room_status(
            db=db,
            room_id=room.id,
        )

        room_items.append(
            {
                "room": room,
                "status": room_status.status,
                "remarks": room_status.remarks,
                "updated_by": room_status.updated_by,
                "updated_at": room_status.updated_at,
            }
        )

    db.commit()

    return templates.TemplateResponse(
        "hotel_operations/room_statuses.html",
        {
            "request": request,
            "room_items": room_items,
            "room_statuses": ROOM_STATUSES,
        },
    )


@router.get("/housekeeping")
async def hotel_operations_housekeeping_page(
    request: Request,
    room_id: int | None = None,
    staff_id: int | None = None,
    task_status: str | None = None,
    task_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(HousekeepingTask)

    if room_id is not None:
        query = query.filter(
            HousekeepingTask.room_id == room_id
        )

    if staff_id is not None:
        query = query.filter(
            HousekeepingTask.staff_id == staff_id
        )

    normalized_task_status = None
    normalized_task_type = None

    if task_status:
        normalized_task_status = HotelOperationsService.normalize(
            task_status
        )
        query = query.filter(
            HousekeepingTask.status == normalized_task_status
        )

    if task_type:
        normalized_task_type = HotelOperationsService.normalize(
            task_type
        )
        query = query.filter(
            HousekeepingTask.task_type == normalized_task_type
        )

    tasks = (
        query.order_by(HousekeepingTask.created_at.desc())
        .all()
    )

    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    staff_members = (
        db.query(HotelStaff)
        .filter(HotelStaff.is_active.is_(True))
        .order_by(HotelStaff.staff_name.asc())
        .all()
    )

    return templates.TemplateResponse(
        "hotel_operations/housekeeping.html",
        {
            "request": request,
            "tasks": tasks,
            "rooms": rooms,
            "staff_members": staff_members,
            "task_statuses": TASK_STATUSES,
            "task_types": TASK_TYPES,
            "task_priorities": TASK_PRIORITIES,
            "selected_room_id": room_id,
            "selected_staff_id": staff_id,
            "selected_task_status": normalized_task_status,
            "selected_task_type": normalized_task_type,
        },
    )


@router.get("/staff-management")
async def hotel_operations_staff_page(
    request: Request,
    db: Session = Depends(get_db),
):
    staff_members = (
        db.query(HotelStaff)
        .order_by(
            HotelStaff.department.asc(),
            HotelStaff.staff_name.asc(),
        )
        .all()
    )

    return templates.TemplateResponse(
        "hotel_operations/staff.html",
        {
            "request": request,
            "staff_members": staff_members,
            "staff_departments": STAFF_DEPARTMENTS,
        },
    )


@router.post("/initialize-room-statuses")
async def initialize_room_statuses(
    request: Request,
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    created = 0

    for room in rooms:
        existing = (
            db.query(HotelRoomStatus)
            .filter(HotelRoomStatus.room_id == room.id)
            .first()
        )

        if existing is None:
            db.add(
                HotelRoomStatus(
                    room_id=room.id,
                    status="VACANT_CLEAN",
                    remarks="Initial room status",
                    updated_by=current_user_name(request),
                )
            )
            created += 1

    db.commit()

    if request.headers.get("accept", "").startswith("text/html"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url="/hotel-operations/rooms",
            status_code=303,
        )

    return {
        "status": "success",
        "rooms_checked": len(rooms),
        "statuses_created": created,
    }


@router.get("/room-statuses")
async def list_room_statuses(
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    payload = []

    for room in rooms:
        room_status = HotelOperationsService.ensure_room_status(
            db=db,
            room_id=room.id,
        )

        payload.append(
            {
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": (
                    room.room_type.name
                    if room.room_type is not None
                    else None
                ),
                "status": room_status.status,
                "remarks": room_status.remarks,
                "updated_by": room_status.updated_by,
                "updated_at": room_status.updated_at,
            }
        )

    db.commit()

    return {
        "count": len(payload),
        "items": payload,
    }


@router.post("/room-statuses/{room_id}")
async def update_room_status(
    room_id: int,
    request: Request,
    status: str = Form(...),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    HotelOperationsService.get_room_or_404(
        db=db,
        room_id=room_id,
    )

    normalized_status = HotelOperationsService.normalize(status)

    if normalized_status not in ROOM_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid room status",
        )

    room_status = HotelOperationsService.set_room_status(
        db=db,
        room_id=room_id,
        status=normalized_status,
        remarks=remarks.strip() or None,
        updated_by=current_user_name(request),
    )

    db.commit()
    db.refresh(room_status)

    if request.headers.get("accept", "").startswith("text/html"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url="/hotel-operations/rooms",
            status_code=303,
        )

    return {
        "status": "success",
        "room_status_id": room_status.id,
        "room_id": room_status.room_id,
        "room_status": room_status.status,
    }


@router.get("/staff")
async def list_hotel_staff(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(HotelStaff)

    if active_only:
        query = query.filter(
            HotelStaff.is_active.is_(True)
        )

    staff_members = (
        query.order_by(
            HotelStaff.department.asc(),
            HotelStaff.staff_name.asc(),
        )
        .all()
    )

    return {
        "count": len(staff_members),
        "items": [
            {
                "id": staff.id,
                "staff_code": staff.staff_code,
                "staff_name": staff.staff_name,
                "mobile": staff.mobile,
                "department": staff.department,
                "designation": staff.designation,
                "is_active": staff.is_active,
            }
            for staff in staff_members
        ],
    }


@router.post("/staff")
async def create_hotel_staff(
    staff_code: str = Form(...),
    staff_name: str = Form(...),
    mobile: str = Form(""),
    department: str = Form("HOUSEKEEPING"),
    designation: str = Form(""),
    db: Session = Depends(get_db),
):
    normalized_code = staff_code.strip().upper()
    normalized_department = HotelOperationsService.normalize(
        department
    )

    if not normalized_code:
        raise HTTPException(
            status_code=400,
            detail="Staff code is required",
        )

    if not staff_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Staff name is required",
        )

    if normalized_department not in STAFF_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail="Invalid staff department",
        )

    existing = (
        db.query(HotelStaff)
        .filter(HotelStaff.staff_code == normalized_code)
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Staff code already exists",
        )

    staff = HotelStaff(
        staff_code=normalized_code,
        staff_name=staff_name.strip(),
        mobile=mobile.strip() or None,
        department=normalized_department,
        designation=designation.strip() or None,
        is_active=True,
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/hotel-operations/staff-management",
        status_code=303,
    )


@router.post("/staff/{staff_id}")
async def update_hotel_staff(
    staff_id: int,
    staff_name: str = Form(...),
    mobile: str = Form(""),
    department: str = Form(...),
    designation: str = Form(""),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
):
    staff = HotelOperationsService.get_staff_or_404(
        db=db,
        staff_id=staff_id,
    )

    normalized_department = HotelOperationsService.normalize(
        department
    )

    if normalized_department not in STAFF_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail="Invalid staff department",
        )

    if not staff_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Staff name is required",
        )

    staff.staff_name = staff_name.strip()
    staff.mobile = mobile.strip() or None
    staff.department = normalized_department
    staff.designation = designation.strip() or None
    staff.is_active = is_active

    db.commit()

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/hotel-operations/staff-management",
        status_code=303,
    )


@router.get("/housekeeping/tasks")
async def list_housekeeping_tasks(
    room_id: int | None = None,
    staff_id: int | None = None,
    task_status: str | None = None,
    task_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(HousekeepingTask)

    if room_id is not None:
        query = query.filter(
            HousekeepingTask.room_id == room_id
        )

    if staff_id is not None:
        query = query.filter(
            HousekeepingTask.staff_id == staff_id
        )

    if task_status:
        normalized_status = HotelOperationsService.normalize(
            task_status
        )

        if normalized_status not in TASK_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid task status filter",
            )

        query = query.filter(
            HousekeepingTask.status == normalized_status
        )

    if task_type:
        normalized_type = HotelOperationsService.normalize(
            task_type
        )

        if normalized_type not in TASK_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid task type filter",
            )

        query = query.filter(
            HousekeepingTask.task_type == normalized_type
        )

    tasks = (
        query.order_by(
            HousekeepingTask.created_at.desc()
        )
        .all()
    )

    return {
        "count": len(tasks),
        "items": [
            {
                "id": task.id,
                "room_id": task.room_id,
                "room_number": (
                    task.room.room_number
                    if task.room is not None
                    else None
                ),
                "staff_id": task.staff_id,
                "staff_name": (
                    task.staff.staff_name
                    if task.staff is not None
                    else None
                ),
                "task_type": task.task_type,
                "priority": task.priority,
                "status": task.status,
                "remarks": task.remarks,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "created_at": task.created_at,
            }
            for task in tasks
        ],
    }


@router.post("/housekeeping/tasks")
async def create_housekeeping_task(
    room_id: int = Form(...),
    task_type: str = Form(...),
    priority: str = Form("NORMAL"),
    staff_id: int | None = Form(None),
    remarks: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
):
    HotelOperationsService.get_room_or_404(
        db=db,
        room_id=room_id,
    )

    normalized_type = HotelOperationsService.normalize(
        task_type
    )
    normalized_priority = HotelOperationsService.normalize(
        priority
    )

    if normalized_type not in TASK_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid task type",
        )

    if normalized_priority not in TASK_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid task priority",
        )

    assigned_staff = None

    if staff_id is not None:
        assigned_staff = HotelOperationsService.get_staff_or_404(
            db=db,
            staff_id=staff_id,
        )

        if not assigned_staff.is_active:
            raise HTTPException(
                status_code=409,
                detail="Selected hotel staff is inactive",
            )

    HotelOperationsService.ensure_no_duplicate_active_task(
        db=db,
        room_id=room_id,
        task_type=normalized_type,
    )

    initial_status = (
        "ASSIGNED"
        if assigned_staff is not None
        else "PENDING"
    )

    task = HousekeepingTask(
        room_id=room_id,
        staff_id=staff_id,
        task_type=normalized_type,
        priority=normalized_priority,
        status=initial_status,
        remarks=remarks.strip() or None,
    )

    db.add(task)
    db.flush()

    HotelOperationsService.set_room_status(
        db=db,
        room_id=room_id,
        status=HotelOperationsService.initial_room_status_for_task(
            normalized_type
        ),
        remarks=f"{normalized_type.title()} task created",
        updated_by=(
            current_user_name(request)
            if request is not None
            else None
        ),
    )

    db.commit()
    db.refresh(task)

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/hotel-operations/housekeeping",
        status_code=303,
    )


@router.post("/housekeeping/tasks/{task_id}")
async def update_housekeeping_task(
    task_id: int,
    priority: str = Form(...),
    staff_id: int | None = Form(None),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    task = HotelOperationsService.get_task_or_404(
        db=db,
        task_id=task_id,
    )

    if task.status in {"COMPLETED", "CANCELLED"}:
        raise HTTPException(
            status_code=409,
            detail="Completed or cancelled tasks cannot be edited",
        )

    normalized_priority = HotelOperationsService.normalize(
        priority
    )

    if normalized_priority not in TASK_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid task priority",
        )

    if staff_id is not None:
        staff = HotelOperationsService.get_staff_or_404(
            db=db,
            staff_id=staff_id,
        )

        if not staff.is_active:
            raise HTTPException(
                status_code=409,
                detail="Selected hotel staff is inactive",
            )

        task.staff_id = staff_id

        if task.status == "PENDING":
            task.status = "ASSIGNED"

    else:
        task.staff_id = None

        if task.status == "ASSIGNED":
            task.status = "PENDING"

    task.priority = normalized_priority
    task.remarks = remarks.strip() or None

    db.commit()

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/hotel-operations/housekeeping",
        status_code=303,
    )


@router.post("/housekeeping/tasks/{task_id}/status")
async def update_housekeeping_task_status(
    task_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    task = HotelOperationsService.get_task_or_404(
        db=db,
        task_id=task_id,
    )

    normalized_status = HotelOperationsService.normalize(
        status
    )

    if normalized_status not in TASK_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid task status",
        )

    if (
        normalized_status in {"ASSIGNED", "IN_PROGRESS"}
        and task.staff_id is None
    ):
        raise HTTPException(
            status_code=409,
            detail="Assign an active staff member before starting the task",
        )

    HotelOperationsService.apply_task_status(
        db=db,
        task=task,
        new_status=normalized_status,
        updated_by=current_user_name(request),
    )

    db.commit()

    return {
        "status": "success",
        "task_id": task.id,
        "task_status": task.status,
    }


@router.delete("/housekeeping/tasks/{task_id}")
async def delete_housekeeping_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = HotelOperationsService.get_task_or_404(
        db=db,
        task_id=task_id,
    )

    if task.status not in {"PENDING", "CANCELLED"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only pending or cancelled tasks can be deleted"
            ),
        )

    db.delete(task)
    db.commit()

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/hotel-operations/housekeeping",
        status_code=303,
    )


@router.get("/inventory")
async def hotel_inventory_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    items = (
        db.query(HotelInventoryItem)
        .filter(HotelInventoryItem.is_active.is_(True))
        .order_by(
            HotelInventoryItem.category.asc(),
            HotelInventoryItem.item_name.asc(),
        )
        .all()
    )

    total_items = len(items)

    healthy_stock = sum(
        1
        for item in items
        if Decimal(item.current_stock) > Decimal(item.minimum_stock)
    )

    low_stock = sum(
        1
        for item in items
        if Decimal(item.current_stock) > Decimal("0")
        and Decimal(item.current_stock) <= Decimal(item.minimum_stock)
    )

    out_stock = sum(
        1
        for item in items
        if Decimal(item.current_stock) <= Decimal("0")
    )

    return templates.TemplateResponse(
        "hotel_inventory/dashboard.html",
        {
            "request": request,
            "items": items,
            "total_items": total_items,
            "healthy_stock": healthy_stock,
            "low_stock": low_stock,
            "out_stock": out_stock,
        },
    )


@router.get("/inventory/items/create")
async def hotel_inventory_item_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        "hotel_inventory/create_item.html",
        {
            "request": request,
        },
    )


@router.post("/inventory/items/create")
async def hotel_inventory_item_create(
    item_code: str = Form(...),
    item_name: str = Form(...),
    category: str = Form(...),
    unit: str = Form("Nos"),
    minimum_stock: str = Form("0"),
    opening_stock: str = Form("0"),
    db: Session = Depends(get_db),
):
    normalized_code = item_code.strip().upper()
    normalized_name = item_name.strip()
    normalized_category = category.strip()
    normalized_unit = unit.strip() or "Nos"

    if not normalized_code:
        raise HTTPException(
            status_code=400,
            detail="Item code is required.",
        )

    if not normalized_name:
        raise HTTPException(
            status_code=400,
            detail="Item name is required.",
        )

    if not normalized_category:
        raise HTTPException(
            status_code=400,
            detail="Category is required.",
        )

    existing_item = (
        db.query(HotelInventoryItem)
        .filter(HotelInventoryItem.item_code == normalized_code)
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=400,
            detail="Inventory item code already exists.",
        )

    minimum_quantity = parse_inventory_quantity(
        minimum_stock,
        "Minimum stock",
        allow_zero=True,
    )

    opening_quantity = parse_inventory_quantity(
        opening_stock,
        "Opening stock",
        allow_zero=True,
    )

    item = HotelInventoryItem(
        item_code=normalized_code,
        item_name=normalized_name,
        category=normalized_category,
        unit=normalized_unit,
        minimum_stock=minimum_quantity,
        current_stock=opening_quantity,
        is_active=True,
    )

    db.add(item)
    db.flush()

    if opening_quantity > 0:
        transaction = HotelInventoryTransaction(
            inventory_item_id=item.id,
            transaction_type="STOCK_IN",
            quantity=opening_quantity,
            balance_after=opening_quantity,
            reference_no="OPENING-STOCK",
            remarks="Opening inventory balance",
        )

        db.add(transaction)

    db.commit()

    return RedirectResponse(
        url="/hotel-operations/inventory",
        status_code=303,
    )


@router.get("/inventory/{item_id}/ledger")
async def hotel_inventory_ledger(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    item = (
        db.query(HotelInventoryItem)
        .filter(HotelInventoryItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    transactions = (
        db.query(HotelInventoryTransaction)
        .filter(
            HotelInventoryTransaction.inventory_item_id == item_id
        )
        .order_by(
            HotelInventoryTransaction.created_at.desc(),
            HotelInventoryTransaction.id.desc(),
        )
        .all()
    )

    return templates.TemplateResponse(
        "hotel_inventory/ledger.html",
        {
            "request": request,
            "item": item,
            "transactions": transactions,
        },
    )


@router.post("/inventory/{item_id}/transaction")
async def hotel_inventory_transaction_create(
    item_id: int,
    transaction_type: str = Form(...),
    quantity: str = Form(...),
    reference_no: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    item = (
        db.query(HotelInventoryItem)
        .filter(HotelInventoryItem.id == item_id)
        .with_for_update()
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    if not item.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inventory item is inactive.",
        )

    normalized_type = normalize_inventory_transaction_type(
        transaction_type
    )

    transaction_quantity = parse_inventory_quantity(
        quantity,
        "Quantity",
    )

    current_balance = Decimal(item.current_stock)
    direction = inventory_transaction_direction(normalized_type)

    new_balance = (
        current_balance
        + transaction_quantity
        if direction == 1
        else current_balance - transaction_quantity
    )

    if new_balance < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient stock. "
                f"Available balance is {current_balance} {item.unit}."
            ),
        )

    new_balance = new_balance.quantize(Decimal("0.01"))

    item.current_stock = new_balance

    transaction = HotelInventoryTransaction(
        inventory_item_id=item.id,
        transaction_type=normalized_type,
        quantity=transaction_quantity,
        balance_after=new_balance,
        reference_no=reference_no.strip() or None,
        remarks=remarks.strip() or None,
    )

    db.add(transaction)
    db.commit()

    return RedirectResponse(
        url=f"/hotel-operations/inventory/{item.id}/ledger",
        status_code=303,
    )


@router.post("/inventory/{item_id}/toggle-status")
async def hotel_inventory_item_toggle_status(
    item_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(HotelInventoryItem)
        .filter(HotelInventoryItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    item.is_active = not item.is_active
    db.commit()

    return RedirectResponse(
        url="/hotel-operations/inventory",
        status_code=303,
    )
@router.get("/laundry")
async def hotel_laundry_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    batches = (
        db.query(HotelLaundryBatch)
        .order_by(
            HotelLaundryBatch.batch_date.desc(),
            HotelLaundryBatch.id.desc(),
        )
        .all()
    )

    status_counts = {
        status: 0
        for status in LAUNDRY_BATCH_STATUSES
    }

    for batch in batches:
        status_counts[batch.status] = (
            status_counts.get(batch.status, 0)
            + 1
        )

    active_statuses = {
        "COLLECTED",
        "SENT_TO_LAUNDRY",
        "IN_PROCESS",
        "PARTIALLY_RETURNED",
    }

    active_batches = sum(
        1
        for batch in batches
        if batch.status in active_statuses
    )

    completed_batches = sum(
        1
        for batch in batches
        if batch.status == "COMPLETED"
    )

    attention_batches = sum(
        1
        for batch in batches
        if (
            batch.status == "PARTIALLY_RETURNED"
            or float(batch.damaged_quantity or 0) > 0
            or float(batch.missing_quantity or 0) > 0
        )
    )

    total_issued = sum(
        float(batch.total_quantity or 0)
        for batch in batches
    )

    total_clean = sum(
        float(batch.clean_quantity or 0)
        for batch in batches
    )

    total_damaged = sum(
        float(batch.damaged_quantity or 0)
        for batch in batches
    )

    total_missing = sum(
        float(batch.missing_quantity or 0)
        for batch in batches
    )

    recent_batches = batches[:50]

    return templates.TemplateResponse(
        "hotel_laundry/dashboard.html",
        {
            "request": request,
            "batches": recent_batches,
            "total_batches": len(batches),
            "active_batches": active_batches,
            "completed_batches": completed_batches,
            "attention_batches": attention_batches,
            "total_issued": total_issued,
            "total_clean": total_clean,
            "total_damaged": total_damaged,
            "total_missing": total_missing,
            "status_counts": status_counts,
        },
    )


@router.get("/laundry/create")
async def hotel_laundry_create_page(
    request: Request,
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active.is_(True))
        .order_by(Room.room_number.asc())
        .all()
    )

    bookings = (
        db.query(Booking)
        .filter(
            Booking.status.in_(
                [
                    "CONFIRMED",
                    "CHECKED_IN",
                    "ACTIVE",
                ]
            )
        )
        .order_by(
            Booking.check_in_at.desc()
        )
        .limit(100)
        .all()
    )

    linen_items = (
        db.query(HotelInventoryItem)
        .filter(
            HotelInventoryItem.is_active.is_(True),
            HotelInventoryItem.category.in_(
                [
                    "LINEN",
                    "BATHROOM",
                    "HOUSEKEEPING",
                ]
            ),
        )
        .order_by(
            HotelInventoryItem.category.asc(),
            HotelInventoryItem.item_name.asc(),
        )
        .all()
    )

    return templates.TemplateResponse(
        "hotel_laundry/create.html",
        {
            "request": request,
            "rooms": rooms,
            "bookings": bookings,
            "linen_items": linen_items,
            "source_types": LAUNDRY_SOURCE_TYPES,
        },
    )


@router.post("/laundry/create")
async def hotel_laundry_create(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()

    source_type = normalize_laundry_source_type(
        str(
            form.get("source_type")
            or "GENERAL"
        )
    )

    room_id_value = str(
        form.get("room_id")
        or ""
    ).strip()

    booking_id_value = str(
        form.get("booking_id")
        or ""
    ).strip()

    room_id = (
        int(room_id_value)
        if room_id_value
        else None
    )

    booking_id = (
        int(booking_id_value)
        if booking_id_value
        else None
    )

    if room_id is not None:
        room = (
            db.query(Room)
            .filter(
                Room.id == room_id,
                Room.is_active.is_(True),
            )
            .first()
        )

        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found.",
            )

    if booking_id is not None:
        booking = (
            db.query(Booking)
            .filter(
                Booking.id == booking_id
            )
            .first()
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found.",
            )

    inventory_item_ids = form.getlist(
        "inventory_item_id"
    )

    issued_quantities = form.getlist(
        "issued_quantity"
    )

    item_remarks = form.getlist(
        "item_remarks"
    )

    if not inventory_item_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one laundry item "
                "is required."
            ),
        )

    if len(inventory_item_ids) != len(
        issued_quantities
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Laundry item quantities are "
                "incomplete."
            ),
        )

    parsed_items: list[
        tuple[
            HotelInventoryItem,
            Decimal,
            str | None,
        ]
    ] = []

    used_item_ids: set[int] = set()
    total_quantity = Decimal("0.00")

    for index, raw_item_id in enumerate(
        inventory_item_ids
    ):
        normalized_item_id = str(
            raw_item_id
        ).strip()

        if not normalized_item_id:
            continue

        try:
            inventory_item_id = int(
                normalized_item_id
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid inventory item."
                ),
            ) from error

        if inventory_item_id in used_item_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The same inventory item "
                    "cannot be entered twice."
                ),
            )

        quantity = parse_inventory_quantity(
            str(
                issued_quantities[index]
            ),
            "Issued quantity",
        )

        inventory_item = (
            db.query(HotelInventoryItem)
            .filter(
                HotelInventoryItem.id
                == inventory_item_id
            )
            .with_for_update()
            .first()
        )

        if not inventory_item:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Inventory item not found."
                ),
            )

        if not inventory_item.is_active:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{inventory_item.item_name} "
                    f"is inactive."
                ),
            )

        remarks_value = (
            str(item_remarks[index]).strip()
            if index < len(item_remarks)
            else ""
        )

        parsed_items.append(
            (
                inventory_item,
                quantity,
                remarks_value or None,
            )
        )

        used_item_ids.add(
            inventory_item_id
        )

        total_quantity += quantity

    if not parsed_items:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one valid laundry "
                "item is required."
            ),
        )

    batch_no = generate_laundry_batch_no(
        db
    )

    batch = HotelLaundryBatch(
        batch_no=batch_no,
        batch_date=datetime.utcnow(),
        source_type=source_type,
        room_id=room_id,
        booking_id=booking_id,
        status="COLLECTED",
        vendor_name=(
            str(
                form.get("vendor_name")
                or ""
            ).strip()
            or None
        ),
        expected_return_at=(
            parse_optional_datetime(
                str(
                    form.get(
                        "expected_return_at"
                    )
                    or ""
                ),
                "Expected return",
            )
        ),
        total_quantity=total_quantity,
        clean_quantity=Decimal("0.00"),
        damaged_quantity=Decimal("0.00"),
        missing_quantity=Decimal("0.00"),
        remarks=(
            str(
                form.get("remarks")
                or ""
            ).strip()
            or None
        ),
        created_by=current_user_name(
            request
        ),
    )

    db.add(batch)
    db.flush()

    for (
        inventory_item,
        quantity,
        remarks_value,
    ) in parsed_items:
        batch_item = HotelLaundryBatchItem(
            laundry_batch_id=batch.id,
            inventory_item_id=(
                inventory_item.id
            ),
            issued_quantity=quantity,
            returned_quantity=(
                Decimal("0.00")
            ),
            clean_quantity=(
                Decimal("0.00")
            ),
            damaged_quantity=(
                Decimal("0.00")
            ),
            missing_quantity=(
                Decimal("0.00")
            ),
            remarks=remarks_value,
        )

        db.add(batch_item)

        apply_laundry_inventory_movement(
            db=db,
            inventory_item=inventory_item,
            transaction_type="LINEN_ISSUE",
            quantity=quantity,
            reference_no=batch.batch_no,
            remarks=(
                "Laundry collection"
                + (
                    f" - Room "
                    f"{batch.room.room_number}"
                    if batch.room
                    else ""
                )
            ),
        )

    db.commit()

    return RedirectResponse(
        url=(
            f"/hotel-operations/laundry/"
            f"{batch.id}"
        ),
        status_code=303,
    )


@router.get("/laundry/{batch_id}")
async def hotel_laundry_view(
    batch_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    batch = (
        db.query(HotelLaundryBatch)
        .filter(
            HotelLaundryBatch.id
            == batch_id
        )
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Laundry batch not found.",
        )

    return templates.TemplateResponse(
        "hotel_laundry/view.html",
        {
            "request": request,
            "batch": batch,
            "statuses": LAUNDRY_BATCH_STATUSES,
        },
    )


@router.post("/laundry/{batch_id}/send")
async def hotel_laundry_send(
    batch_id: int,
    vendor_name: str = Form(""),
    expected_return_at: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    batch = (
        db.query(HotelLaundryBatch)
        .filter(
            HotelLaundryBatch.id
            == batch_id
        )
        .with_for_update()
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Laundry batch not found.",
        )

    if batch.status not in {
        "COLLECTED",
        "IN_PROCESS",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only collected or in-process "
                "batches can be sent."
            ),
        )

    batch.status = "SENT_TO_LAUNDRY"
    batch.sent_at = datetime.utcnow()
    batch.vendor_name = (
        vendor_name.strip()
        or batch.vendor_name
    )

    parsed_expected_return = (
        parse_optional_datetime(
            expected_return_at,
            "Expected return",
        )
    )

    if parsed_expected_return:
        batch.expected_return_at = (
            parsed_expected_return
        )

    if remarks.strip():
        batch.remarks = remarks.strip()

    db.commit()

    return RedirectResponse(
        url=(
            f"/hotel-operations/laundry/"
            f"{batch.id}"
        ),
        status_code=303,
    )


@router.post("/laundry/{batch_id}/receive")
async def hotel_laundry_receive(
    batch_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()

    batch = (
        db.query(HotelLaundryBatch)
        .filter(
            HotelLaundryBatch.id
            == batch_id
        )
        .with_for_update()
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Laundry batch not found.",
        )

    if batch.status in {
        "COMPLETED",
        "CANCELLED",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "This laundry batch is already "
                "closed."
            ),
        )

    item_ids = form.getlist(
        "batch_item_id"
    )

    clean_values = form.getlist(
        "clean_quantity"
    )

    damaged_values = form.getlist(
        "damaged_quantity"
    )

    missing_values = form.getlist(
        "missing_quantity"
    )

    if not item_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "No laundry return items "
                "were submitted."
            ),
        )

    total_clean = Decimal("0.00")
    total_damaged = Decimal("0.00")
    total_missing = Decimal("0.00")
    total_returned = Decimal("0.00")

    for index, raw_batch_item_id in enumerate(
        item_ids
    ):
        try:
            batch_item_id = int(
                str(raw_batch_item_id)
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid laundry batch item."
                ),
            ) from error

        batch_item = (
            db.query(HotelLaundryBatchItem)
            .filter(
                HotelLaundryBatchItem.id
                == batch_item_id,
                HotelLaundryBatchItem.laundry_batch_id
                == batch.id,
            )
            .with_for_update()
            .first()
        )

        if not batch_item:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Laundry batch item "
                    "not found."
                ),
            )

        clean_quantity = (
            parse_inventory_quantity(
                str(clean_values[index]),
                "Clean quantity",
                allow_zero=True,
            )
            if index < len(clean_values)
            else Decimal("0.00")
        )

        damaged_quantity = (
            parse_inventory_quantity(
                str(damaged_values[index]),
                "Damaged quantity",
                allow_zero=True,
            )
            if index < len(damaged_values)
            else Decimal("0.00")
        )

        missing_quantity = (
            parse_inventory_quantity(
                str(missing_values[index]),
                "Missing quantity",
                allow_zero=True,
            )
            if index < len(missing_values)
            else Decimal("0.00")
        )

        submitted_total = (
            clean_quantity
            + damaged_quantity
            + missing_quantity
        )

        remaining_quantity = (
            Decimal(
                batch_item.issued_quantity
            )
            - Decimal(
                batch_item.returned_quantity
            )
        ).quantize(
            Decimal("0.01")
        )

        if submitted_total > remaining_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Return quantity for "
                    f"{batch_item.inventory_item.item_name} "
                    f"exceeds remaining quantity "
                    f"{remaining_quantity}."
                ),
            )

        if submitted_total <= 0:
            continue

        batch_item.clean_quantity = (
            Decimal(
                batch_item.clean_quantity
            )
            + clean_quantity
        )

        batch_item.damaged_quantity = (
            Decimal(
                batch_item.damaged_quantity
            )
            + damaged_quantity
        )

        batch_item.missing_quantity = (
            Decimal(
                batch_item.missing_quantity
            )
            + missing_quantity
        )

        batch_item.returned_quantity = (
            Decimal(
                batch_item.returned_quantity
            )
            + submitted_total
        )

        if clean_quantity > 0:
            inventory_item = (
                db.query(HotelInventoryItem)
                .filter(
                    HotelInventoryItem.id
                    == batch_item.inventory_item_id
                )
                .with_for_update()
                .first()
            )

            apply_laundry_inventory_movement(
                db=db,
                inventory_item=inventory_item,
                transaction_type=(
                    "LINEN_RETURN"
                ),
                quantity=clean_quantity,
                reference_no=batch.batch_no,
                remarks=(
                    "Clean linen returned "
                    "from laundry"
                ),
            )

        total_clean += clean_quantity
        total_damaged += damaged_quantity
        total_missing += missing_quantity
        total_returned += submitted_total

    batch.clean_quantity = (
        Decimal(batch.clean_quantity)
        + total_clean
    )

    batch.damaged_quantity = (
        Decimal(batch.damaged_quantity)
        + total_damaged
    )

    batch.missing_quantity = (
        Decimal(batch.missing_quantity)
        + total_missing
    )

    complete = all(
        Decimal(item.returned_quantity)
        >= Decimal(item.issued_quantity)
        for item in batch.items
    )

    if complete:
        batch.status = "COMPLETED"
        batch.returned_at = datetime.utcnow()
    elif total_returned > 0:
        batch.status = "PARTIALLY_RETURNED"

    remarks = str(
        form.get("remarks")
        or ""
    ).strip()

    if remarks:
        batch.remarks = remarks

    db.commit()

    return RedirectResponse(
        url=(
            f"/hotel-operations/laundry/"
            f"{batch.id}"
        ),
        status_code=303,
    )


@router.post("/laundry/{batch_id}/status")
async def hotel_laundry_update_status(
    batch_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    batch = (
        db.query(HotelLaundryBatch)
        .filter(
            HotelLaundryBatch.id
            == batch_id
        )
        .with_for_update()
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Laundry batch not found.",
        )

    normalized_status = (
        normalize_laundry_status(status)
    )

    if normalized_status == "COMPLETED":
        complete = all(
            Decimal(item.returned_quantity)
            >= Decimal(item.issued_quantity)
            for item in batch.items
        )

        if not complete:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A laundry batch cannot be "
                    "completed while items are "
                    "still pending."
                ),
            )

        batch.returned_at = (
            batch.returned_at
            or datetime.utcnow()
        )

    batch.status = normalized_status

    db.commit()

    return RedirectResponse(
        url=(
            f"/hotel-operations/laundry/"
            f"{batch.id}"
        ),
        status_code=303,
    )
