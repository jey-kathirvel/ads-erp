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
