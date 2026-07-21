#!/usr/bin/env bash
set -euo pipefail

cd /opt/ads-erp-phase2 || exit 1

CURRENT_BRANCH="$(git branch --show-current)"
if [ "$CURRENT_BRANCH" != "ui-buttons" ]; then
    echo "ERROR: Current branch is '$CURRENT_BRANCH'. Switch to ui-buttons first."
    exit 1
fi

echo "===== PATCH-HOTEL-OPS-002 START ====="

mkdir -p app/hotel_operations

cp -a app/routes/router.py "app/routes/router.py.patch-hotel-ops-002.bak"

cat > app/hotel_operations/constants.py <<'PY'
ROOM_STATUSES = {
    "VACANT_CLEAN",
    "VACANT_DIRTY",
    "OCCUPIED",
    "OCCUPIED_DIRTY",
    "READY_FOR_CHECKIN",
    "LAUNDRY",
    "MAINTENANCE",
    "OUT_OF_ORDER",
    "INSPECTION",
}

TASK_TYPES = {
    "CLEANING",
    "LAUNDRY",
    "MAINTENANCE",
    "INSPECTION",
}

TASK_PRIORITIES = {
    "LOW",
    "NORMAL",
    "HIGH",
    "URGENT",
}

TASK_STATUSES = {
    "PENDING",
    "ASSIGNED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
}

STAFF_DEPARTMENTS = {
    "HOUSEKEEPING",
    "LAUNDRY",
    "MAINTENANCE",
    "SUPERVISION",
}

ACTIVE_TASK_STATUSES = {
    "PENDING",
    "ASSIGNED",
    "IN_PROGRESS",
}
PY

cat > app/hotel_operations/service.py <<'PY'
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.booking.models import Room
from app.hotel_operations.constants import ACTIVE_TASK_STATUSES
from app.hotel_operations.models import (
    HotelRoomStatus,
    HotelStaff,
    HousekeepingTask,
)


class HotelOperationsService:
    @staticmethod
    def normalize(value: str) -> str:
        return value.strip().upper().replace(" ", "_")

    @staticmethod
    def get_room_or_404(
        db: Session,
        room_id: int,
    ) -> Room:
        room = (
            db.query(Room)
            .filter(
                Room.id == room_id,
                Room.is_active.is_(True),
            )
            .first()
        )

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Active room not found",
            )

        return room

    @staticmethod
    def get_staff_or_404(
        db: Session,
        staff_id: int,
    ) -> HotelStaff:
        staff = (
            db.query(HotelStaff)
            .filter(HotelStaff.id == staff_id)
            .first()
        )

        if staff is None:
            raise HTTPException(
                status_code=404,
                detail="Hotel staff not found",
            )

        return staff

    @staticmethod
    def get_task_or_404(
        db: Session,
        task_id: int,
    ) -> HousekeepingTask:
        task = (
            db.query(HousekeepingTask)
            .filter(HousekeepingTask.id == task_id)
            .first()
        )

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Housekeeping task not found",
            )

        return task

    @staticmethod
    def ensure_room_status(
        db: Session,
        room_id: int,
        default_status: str = "VACANT_CLEAN",
    ) -> HotelRoomStatus:
        room_status = (
            db.query(HotelRoomStatus)
            .filter(HotelRoomStatus.room_id == room_id)
            .first()
        )

        if room_status is None:
            room_status = HotelRoomStatus(
                room_id=room_id,
                status=default_status,
            )
            db.add(room_status)
            db.flush()

        return room_status

    @staticmethod
    def set_room_status(
        db: Session,
        room_id: int,
        status: str,
        remarks: str | None = None,
        updated_by: str | None = None,
    ) -> HotelRoomStatus:
        room_status = HotelOperationsService.ensure_room_status(
            db=db,
            room_id=room_id,
        )

        room_status.status = status
        room_status.remarks = remarks
        room_status.updated_by = updated_by

        return room_status

    @staticmethod
    def initial_room_status_for_task(
        task_type: str,
    ) -> str:
        mapping = {
            "CLEANING": "VACANT_DIRTY",
            "LAUNDRY": "LAUNDRY",
            "MAINTENANCE": "MAINTENANCE",
            "INSPECTION": "INSPECTION",
        }

        return mapping[task_type]

    @staticmethod
    def completed_room_status_for_task(
        task_type: str,
    ) -> str:
        mapping = {
            "CLEANING": "READY_FOR_CHECKIN",
            "LAUNDRY": "VACANT_CLEAN",
            "MAINTENANCE": "VACANT_CLEAN",
            "INSPECTION": "READY_FOR_CHECKIN",
        }

        return mapping[task_type]

    @staticmethod
    def ensure_no_duplicate_active_task(
        db: Session,
        room_id: int,
        task_type: str,
        exclude_task_id: int | None = None,
    ) -> None:
        query = (
            db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.room_id == room_id,
                HousekeepingTask.task_type == task_type,
                HousekeepingTask.status.in_(ACTIVE_TASK_STATUSES),
            )
        )

        if exclude_task_id is not None:
            query = query.filter(
                HousekeepingTask.id != exclude_task_id
            )

        if query.first() is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An active task of this type already exists "
                    "for the selected room"
                ),
            )

    @staticmethod
    def apply_task_status(
        db: Session,
        task: HousekeepingTask,
        new_status: str,
        updated_by: str | None = None,
    ) -> None:
        previous_status = task.status
        task.status = new_status

        if new_status == "IN_PROGRESS":
            task.started_at = task.started_at or datetime.utcnow()
            HotelOperationsService.set_room_status(
                db=db,
                room_id=task.room_id,
                status=HotelOperationsService.initial_room_status_for_task(
                    task.task_type
                ),
                remarks=f"{task.task_type.title()} in progress",
                updated_by=updated_by,
            )

        elif new_status == "COMPLETED":
            task.started_at = task.started_at or datetime.utcnow()
            task.completed_at = datetime.utcnow()

            HotelOperationsService.set_room_status(
                db=db,
                room_id=task.room_id,
                status=HotelOperationsService.completed_room_status_for_task(
                    task.task_type
                ),
                remarks=f"{task.task_type.title()} completed",
                updated_by=updated_by,
            )

        elif new_status == "CANCELLED":
            task.completed_at = None

            remaining_active = (
                db.query(HousekeepingTask)
                .filter(
                    HousekeepingTask.room_id == task.room_id,
                    HousekeepingTask.id != task.id,
                    HousekeepingTask.status.in_(
                        ACTIVE_TASK_STATUSES
                    ),
                )
                .first()
            )

            if remaining_active is None:
                HotelOperationsService.set_room_status(
                    db=db,
                    room_id=task.room_id,
                    status="VACANT_CLEAN",
                    remarks="No active housekeeping tasks",
                    updated_by=updated_by,
                )

        elif new_status in {"PENDING", "ASSIGNED"}:
            task.completed_at = None

            HotelOperationsService.set_room_status(
                db=db,
                room_id=task.room_id,
                status=HotelOperationsService.initial_room_status_for_task(
                    task.task_type
                ),
                remarks=f"{task.task_type.title()} task {new_status.lower()}",
                updated_by=updated_by,
            )

        if previous_status == "COMPLETED" and new_status != "COMPLETED":
            task.completed_at = None
PY

cat > app/hotel_operations/routes.py <<'PY'
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import login_required
from app.booking.models import Room
from app.config.database import get_db
from app.hotel_operations.constants import (
    ROOM_STATUSES,
    STAFF_DEPARTMENTS,
    TASK_PRIORITIES,
    TASK_STATUSES,
    TASK_TYPES,
)
from app.hotel_operations.models import (
    HotelRoomStatus,
    HotelStaff,
    HousekeepingTask,
)
from app.hotel_operations.service import HotelOperationsService


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

    return {
        "status": "success",
        "staff_id": staff.id,
        "staff_code": staff.staff_code,
    }


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

    return {
        "status": "success",
        "staff_id": staff.id,
    }


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

    return {
        "status": "success",
        "task_id": task.id,
        "task_status": task.status,
    }


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

    return {
        "status": "success",
        "task_id": task.id,
    }


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

    return {
        "status": "success",
        "deleted_task_id": task_id,
    }
PY

python3 - <<'PY'
from pathlib import Path

path = Path("app/routes/router.py")
text = path.read_text()

import_line = (
    "from app.hotel_operations.routes "
    "import router as hotel_operations_router\n"
)

if import_line not in text:
    anchor = (
        "from app.finance_tools.routes "
        "import router as finance_tools_router\n"
    )

    if anchor not in text:
        raise SystemExit(
            "ERROR: finance_tools router import anchor not found"
        )

    text = text.replace(
        anchor,
        anchor + import_line,
        1,
    )

include_block = (
    "\n# Hotel Operations\n"
    "api_router.include_router(\n"
    "    hotel_operations_router,\n"
    "    tags=[\"Hotel Operations\"],\n"
    ")\n"
)

if "include_router(\n    hotel_operations_router" not in text:
    anchor = (
        "# Booking\n"
        "api_router.include_router("
        "booking_router, tags=[\"Booking\"])\n"
    )

    if anchor not in text:
        raise SystemExit(
            "ERROR: booking router include anchor not found"
        )

    text = text.replace(
        anchor,
        anchor + include_block,
        1,
    )

path.write_text(text)
PY

echo "===== COMPILE VERIFY ====="
./venv/bin/python -m compileall app main.py

echo "===== ROUTER IMPORT VERIFY ====="
./venv/bin/python - <<'PY'
from app.hotel_operations.routes import router
from app.hotel_operations.service import HotelOperationsService

paths = sorted(
    route.path
    for route in router.routes
)

expected = {
    "/hotel-operations/initialize-room-statuses",
    "/hotel-operations/room-statuses",
    "/hotel-operations/room-statuses/{room_id}",
    "/hotel-operations/staff",
    "/hotel-operations/staff/{staff_id}",
    "/hotel-operations/housekeeping/tasks",
    "/hotel-operations/housekeeping/tasks/{task_id}",
    "/hotel-operations/housekeeping/tasks/{task_id}/status",
}

missing = expected - set(paths)
assert not missing, f"Missing routes: {sorted(missing)}"

assert (
    HotelOperationsService.initial_room_status_for_task(
        "CLEANING"
    )
    == "VACANT_DIRTY"
)

assert (
    HotelOperationsService.completed_room_status_for_task(
        "CLEANING"
    )
    == "READY_FOR_CHECKIN"
)

print("PATCH-HOTEL-OPS-002 ROUTES: PASSED")
PY

echo "===== APPLICATION ROUTE VERIFY ====="
./venv/bin/python - <<'PY'
from main import app

paths = {
    route.path
    for route in app.routes
}

required = {
    "/hotel-operations/room-statuses",
    "/hotel-operations/staff",
    "/hotel-operations/housekeeping/tasks",
}

missing = required - paths
assert not missing, f"Missing application routes: {sorted(missing)}"

print("APPLICATION ROUTER REGISTRATION: PASSED")
PY

echo "===== GIT VERIFY ====="
git diff --check
git diff --stat

echo
echo "PATCH-HOTEL-OPS-002 CODE INSTALLED"
echo
echo "NEXT COMMANDS:"
echo "git add app/hotel_operations app/routes/router.py"
echo 'git commit -m "Add housekeeping backend business logic"'
echo "git push origin ui-buttons"
echo "systemctl restart ads-erp"
echo "systemctl status ads-erp --no-pager"
echo
echo "FINAL VERIFY:"
echo "curl -fsS http://127.0.0.1:8000/health"
