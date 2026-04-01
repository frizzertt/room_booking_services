from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.serializers import schedule_to_dict
from app.core.errors import APIError
from app.core.security import Principal
from app.db.models import Room, Schedule
from app.db.session import get_db

router = APIRouter(tags=["Schedules"])


class CreateScheduleRequest(BaseModel):
    daysOfWeek: list[int]
    startTime: str
    endTime: str


def parse_hhmm(value: str):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="invalid time format, expected HH:MM") from exc


def normalize_days(days: list[int]) -> list[int]:
    if not days:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="daysOfWeek must not be empty")

    if any(day < 1 or day > 7 for day in days):
        raise APIError(status_code=400, code="INVALID_REQUEST", message="daysOfWeek values must be in range 1..7")

    return sorted(set(days))


def validate_slot_range(start_time, end_time) -> None:
    if start_time >= end_time:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="startTime must be earlier than endTime")

    minutes = int((datetime.combine(datetime.today(), end_time) - datetime.combine(datetime.today(), start_time)).total_seconds() / 60)
    if minutes % 30 != 0:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="time range must be divisible by 30 minutes")


@router.post("/rooms/{roomId}/schedule/create", status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: CreateScheduleRequest,
    room_id: UUID = Path(alias="roomId"),
    _: Principal = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, str | list[int]]]:
    room = db.get(Room, room_id)
    if room is None:
        raise APIError(status_code=404, code="ROOM_NOT_FOUND", message="room not found")

    existing = db.scalar(select(Schedule).where(Schedule.room_id == room_id))
    if existing is not None:
        raise APIError(
            status_code=409,
            code="SCHEDULE_EXISTS",
            message="schedule for this room already exists and cannot be changed",
        )

    days = normalize_days(payload.daysOfWeek)
    start_time = parse_hhmm(payload.startTime)
    end_time = parse_hhmm(payload.endTime)
    validate_slot_range(start_time, end_time)

    schedule = Schedule(
        room_id=room_id,
        days_of_week=days,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return {"schedule": schedule_to_dict(schedule)}
