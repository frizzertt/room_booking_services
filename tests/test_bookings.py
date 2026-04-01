from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Booking, BookingStatus, Room, Slot, User
from tests.helpers import auth_headers, prepare_bookable_slot


def test_e2e_create_room_schedule_and_booking(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id, _ = prepare_bookable_slot(client, admin, user)

    booking = client.post("/bookings/create", headers=user, json={"slotId": slot_id})
    assert booking.status_code == 201
    assert booking.json()["booking"]["status"] == "active"


def test_e2e_cancel_booking_idempotent(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id, _ = prepare_bookable_slot(client, admin, user)
    booking = client.post("/bookings/create", headers=user, json={"slotId": slot_id})
    booking_id = booking.json()["booking"]["id"]

    cancel_first = client.post(f"/bookings/{booking_id}/cancel", headers=user)
    cancel_second = client.post(f"/bookings/{booking_id}/cancel", headers=user)

    assert cancel_first.status_code == 200
    assert cancel_second.status_code == 200
    assert cancel_first.json()["booking"]["status"] == "cancelled"
    assert cancel_second.json()["booking"]["status"] == "cancelled"


def test_cannot_double_book_same_slot(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id, _ = prepare_bookable_slot(client, admin, user)

    first = client.post("/bookings/create", headers=user, json={"slotId": slot_id})
    second = client.post("/bookings/create", headers=user, json={"slotId": slot_id})

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "SLOT_ALREADY_BOOKED"


def test_admin_cannot_create_booking(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id, _ = prepare_bookable_slot(client, admin, user)

    response = client.post("/bookings/create", headers=admin, json={"slotId": slot_id})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_cannot_book_past_slot(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    room_response = client.post("/rooms/create", headers=admin, json={"name": "Past room"})
    room_id = room_response.json()["room"]["id"]

    past_date = date.today() - timedelta(days=1)
    client.post(
        f"/rooms/{room_id}/schedule/create",
        headers=admin,
        json={"daysOfWeek": [past_date.isoweekday()], "startTime": "09:00", "endTime": "10:00"},
    )

    slots_response = client.get(
        f"/rooms/{room_id}/slots/list",
        headers=user,
        params={"date": past_date.isoformat()},
    )
    slot_id = slots_response.json()["slots"][0]["id"]

    booking_response = client.post("/bookings/create", headers=user, json={"slotId": slot_id})
    assert booking_response.status_code == 400
    assert booking_response.json()["error"]["code"] == "INVALID_REQUEST"


def test_my_bookings_returns_only_future_slots(client, session_factory: sessionmaker):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id, _ = prepare_bookable_slot(client, admin, user)
    client.post("/bookings/create", headers=user, json={"slotId": slot_id})

    with session_factory() as db:
        user_obj = db.get(User, UUID(settings.user_dummy_user_id))
        assert user_obj is not None

        room = Room(name="Past data room")
        db.add(room)
        db.flush()

        past_slot = Slot(
            room_id=room.id,
            start_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2),
            end_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2) + timedelta(minutes=30),
        )
        db.add(past_slot)
        db.flush()

        past_booking = Booking(
            slot_id=past_slot.id,
            user_id=user_obj.id,
            status=BookingStatus.active,
        )
        db.add(past_booking)
        db.commit()

    my = client.get("/bookings/my", headers=user)
    assert my.status_code == 200

    returned_ids = {item["slotId"] for item in my.json()["bookings"]}
    assert slot_id in returned_ids
    assert str(past_slot.id) not in returned_ids


def test_admin_bookings_pagination(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    slot_id_1, _ = prepare_bookable_slot(client, admin, user)
    booking1 = client.post("/bookings/create", headers=user, json={"slotId": slot_id_1})
    assert booking1.status_code == 201

    slot_id_2, _ = prepare_bookable_slot(client, admin, user)
    booking2 = client.post("/bookings/create", headers=user, json={"slotId": slot_id_2})
    assert booking2.status_code == 201

    response = client.get("/bookings/list", headers=admin, params={"page": 1, "pageSize": 1})
    assert response.status_code == 200
    body = response.json()

    assert len(body["bookings"]) == 1
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["pageSize"] == 1
    assert body["pagination"]["total"] >= 2
