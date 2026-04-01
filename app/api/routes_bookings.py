from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.serializers import booking_to_dict
from app.core.errors import APIError
from app.core.security import Principal
from app.db.models import Booking, BookingStatus, Slot, User
from app.db.session import get_db
from app.services.conference import conference_service

router = APIRouter(tags=["Bookings"])


class CreateBookingRequest(BaseModel):
    slotId: UUID
    createConferenceLink: bool = False


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@router.post("/bookings/create", status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: CreateBookingRequest,
    principal: Principal = Depends(require_roles("user")),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, str | None]]:
    user = db.get(User, principal.user_id)
    if user is None:
        raise APIError(status_code=401, code="UNAUTHORIZED", message="user not found")

    slot = db.get(Slot, payload.slotId)
    if slot is None:
        raise APIError(status_code=404, code="SLOT_NOT_FOUND", message="slot not found")

    now = utc_now_naive()
    if slot.start_at < now:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="cannot book slot in the past")

    conference_link = None
    if payload.createConferenceLink:
        conference_link = conference_service.create_link(slot_id=slot.id, user_id=user.id)

    booking = Booking(
        slot_id=slot.id,
        user_id=user.id,
        status=BookingStatus.active,
        conference_link=conference_link,
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise APIError(status_code=409, code="SLOT_ALREADY_BOOKED", message="slot is already booked") from exc

    db.refresh(booking)
    return {"booking": booking_to_dict(booking)}


@router.get("/bookings/list")
def list_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    _: Principal = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    total = db.scalar(select(func.count()).select_from(Booking)) or 0

    stmt = (
        select(Booking)
        .order_by(Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    bookings = list(db.scalars(stmt))

    return {
        "bookings": [booking_to_dict(booking) for booking in bookings],
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
        },
    }


@router.get("/bookings/my")
def list_my_bookings(
    principal: Principal = Depends(require_roles("user")),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str | None]]]:
    now = utc_now_naive()
    stmt = (
        select(Booking)
        .join(Slot, Slot.id == Booking.slot_id)
        .where(
            Booking.user_id == principal.user_id,
            Slot.start_at >= now,
        )
        .order_by(Slot.start_at.asc())
    )
    bookings = list(db.scalars(stmt))
    return {"bookings": [booking_to_dict(booking) for booking in bookings]}


@router.post("/bookings/{bookingId}/cancel")
def cancel_booking(
    booking_id: UUID = Path(alias="bookingId"),
    principal: Principal = Depends(require_roles("user")),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, str | None]]:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise APIError(status_code=404, code="BOOKING_NOT_FOUND", message="booking not found")

    if booking.user_id != principal.user_id:
        raise APIError(status_code=403, code="FORBIDDEN", message="cannot cancel another user's booking")

    if booking.status == BookingStatus.active:
        booking.status = BookingStatus.cancelled
        db.add(booking)
        db.commit()
        db.refresh(booking)

    return {"booking": booking_to_dict(booking)}
