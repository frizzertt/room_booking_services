from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models import Booking, BookingStatus, Schedule, Slot

SLOT_DURATION = timedelta(minutes=30)


def normalize_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def day_bounds(target_date: date) -> tuple[datetime, datetime]:
    day_start = datetime.combine(target_date, time.min)
    day_end = day_start + timedelta(days=1)
    return day_start, day_end


def generate_slots_for_date(db: Session, *, room_id: UUID, schedule: Schedule, target_date: date) -> bool:
    if target_date.isoweekday() not in set(schedule.days_of_week):
        return False

    start_dt = datetime.combine(target_date, schedule.start_time)
    end_dt = datetime.combine(target_date, schedule.end_time)
    if end_dt <= start_dt:
        return False

    day_start, day_end = day_bounds(target_date)
    existing_starts = set(
        normalize_utc_naive(dt)
        for dt in db.scalars(
            select(Slot.start_at).where(
                Slot.room_id == room_id,
                Slot.start_at >= day_start,
                Slot.start_at < day_end,
            )
        )
    )

    created = False
    current = start_dt
    while current + SLOT_DURATION <= end_dt:
        current_normalized = normalize_utc_naive(current)
        if current_normalized not in existing_starts:
            db.add(
                Slot(
                    room_id=room_id,
                    start_at=current_normalized,
                    end_at=normalize_utc_naive(current + SLOT_DURATION),
                )
            )
            created = True
        current += SLOT_DURATION

    if created:
        db.flush()

    return created


def get_available_slots(db: Session, *, room_id: UUID, target_date: date) -> list[Slot]:
    day_start, day_end = day_bounds(target_date)

    stmt = (
        select(Slot)
        .outerjoin(
            Booking,
            and_(
                Booking.slot_id == Slot.id,
                Booking.status == BookingStatus.active,
            ),
        )
        .where(
            Slot.room_id == room_id,
            Slot.start_at >= day_start,
            Slot.start_at < day_end,
            Booking.id.is_(None),
        )
        .order_by(Slot.start_at.asc())
    )
    return list(db.scalars(stmt))
