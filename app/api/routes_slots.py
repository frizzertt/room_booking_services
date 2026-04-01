from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.serializers import slot_to_dict
from app.core.errors import APIError
from app.core.security import Principal
from app.db.models import Room, Schedule
from app.db.session import get_db
from app.services.slots import generate_slots_for_date, get_available_slots

router = APIRouter(tags=["Slots"])


@router.get("/rooms/{roomId}/slots/list")
def list_available_slots(
    room_id: UUID = Path(alias="roomId"),
    target_date: date = Query(alias="date"),
    _: Principal = Depends(require_roles("admin", "user")),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str]]]:
    room = db.get(Room, room_id)
    if room is None:
        raise APIError(status_code=404, code="ROOM_NOT_FOUND", message="room not found")

    schedule = db.scalar(select(Schedule).where(Schedule.room_id == room_id))
    if schedule is None:
        return {"slots": []}

    created = generate_slots_for_date(db, room_id=room_id, schedule=schedule, target_date=target_date)
    if created:
        db.commit()

    slots = get_available_slots(db, room_id=room_id, target_date=target_date)
    return {"slots": [slot_to_dict(slot) for slot in slots]}
