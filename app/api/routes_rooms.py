from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.serializers import room_to_dict
from app.core.errors import APIError
from app.core.security import Principal
from app.db.models import Room
from app.db.session import get_db

router = APIRouter(tags=["Rooms"])


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    capacity: int | None = Field(default=None, ge=1)


@router.get("/rooms/list")
def list_rooms(
    _: Principal = Depends(require_roles("admin", "user")),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str | int | None]]]:
    rooms = list(db.scalars(select(Room).order_by(Room.created_at.asc())))
    return {"rooms": [room_to_dict(room) for room in rooms]}


@router.post("/rooms/create", status_code=status.HTTP_201_CREATED)
def create_room(
    payload: CreateRoomRequest,
    _: Principal = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, str | int | None]]:
    name = payload.name.strip()
    if not name:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="name must not be empty")

    room = Room(
        name=name,
        description=payload.description,
        capacity=payload.capacity,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"room": room_to_dict(room)}
