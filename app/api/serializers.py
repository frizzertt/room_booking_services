from datetime import UTC, datetime

from app.db.models import Booking, Room, Schedule, Slot, User


def to_iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def user_to_dict(user: User) -> dict[str, str | None]:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "createdAt": to_iso_utc(user.created_at),
    }


def room_to_dict(room: Room) -> dict[str, str | int | None]:
    return {
        "id": str(room.id),
        "name": room.name,
        "description": room.description,
        "capacity": room.capacity,
        "createdAt": to_iso_utc(room.created_at),
    }


def schedule_to_dict(schedule: Schedule) -> dict[str, str | list[int]]:
    return {
        "id": str(schedule.id),
        "roomId": str(schedule.room_id),
        "daysOfWeek": list(schedule.days_of_week),
        "startTime": schedule.start_time.strftime("%H:%M"),
        "endTime": schedule.end_time.strftime("%H:%M"),
    }


def slot_to_dict(slot: Slot) -> dict[str, str]:
    return {
        "id": str(slot.id),
        "roomId": str(slot.room_id),
        "start": to_iso_utc(slot.start_at),
        "end": to_iso_utc(slot.end_at),
    }


def booking_to_dict(booking: Booking) -> dict[str, str | None]:
    return {
        "id": str(booking.id),
        "slotId": str(booking.slot_id),
        "userId": str(booking.user_id),
        "status": booking.status.value,
        "conferenceLink": booking.conference_link,
        "createdAt": to_iso_utc(booking.created_at),
    }
