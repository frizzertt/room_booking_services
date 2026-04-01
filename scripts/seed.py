from datetime import date, time, timedelta
from uuid import UUID

from sqlalchemy import select

from app.core.config import settings
from app.db.base import Base
from app.db.models import Role, Room, Schedule, User
from app.db.session import SessionLocal, engine
from app.services.slots import generate_slots_for_date


def ensure_dummy_users(db) -> None:
    admin_id = UUID(settings.admin_dummy_user_id)
    user_id = UUID(settings.user_dummy_user_id)

    if db.get(User, admin_id) is None:
        db.add(
            User(
                id=admin_id,
                email="dummy-admin@example.com",
                role=Role.admin,
                password_hash=None,
            )
        )

    if db.get(User, user_id) is None:
        db.add(
            User(
                id=user_id,
                email="dummy-user@example.com",
                role=Role.user,
                password_hash=None,
            )
        )


def ensure_room_with_schedule(db, *, name: str, description: str, capacity: int) -> Room:
    room = db.scalar(select(Room).where(Room.name == name))
    if room is None:
        room = Room(name=name, description=description, capacity=capacity)
        db.add(room)
        db.flush()

    schedule = db.scalar(select(Schedule).where(Schedule.room_id == room.id))
    if schedule is None:
        schedule = Schedule(
            room_id=room.id,
            days_of_week=[1, 2, 3, 4, 5],
            start_time=time(hour=9, minute=0),
            end_time=time(hour=18, minute=0),
        )
        db.add(schedule)
        db.flush()

    today = date.today()
    for offset in range(0, 7):
        generate_slots_for_date(db, room_id=room.id, schedule=schedule, target_date=today + timedelta(days=offset))

    return room


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        ensure_dummy_users(db)
        ensure_room_with_schedule(
            db,
            name="Mercury",
            description="Small room for quick sync",
            capacity=4,
        )
        ensure_room_with_schedule(
            db,
            name="Venus",
            description="Medium room for team meetings",
            capacity=8,
        )
        ensure_room_with_schedule(
            db,
            name="Jupiter",
            description="Large room for demos",
            capacity=14,
        )
        db.commit()

    print("Seed completed")


if __name__ == "__main__":
    main()
