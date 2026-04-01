from datetime import date, timedelta

from tests.helpers import auth_headers, create_room, create_schedule


def test_user_cannot_create_room(client):
    user = auth_headers(client, "user")
    response = client.post("/rooms/create", headers=user, json={"name": "Forbidden"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_schedule_can_be_created_only_once_and_slots_are_stable(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    room_id = create_room(client, admin)
    target_date = date.today() + timedelta(days=1)
    day = target_date.isoweekday()

    create_schedule(client, admin, room_id, day_of_week=day, start="09:00", end="11:00")

    duplicate = client.post(
        f"/rooms/{room_id}/schedule/create",
        headers=admin,
        json={"daysOfWeek": [day], "startTime": "09:00", "endTime": "11:00"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "SCHEDULE_EXISTS"

    slots_first = client.get(
        f"/rooms/{room_id}/slots/list",
        headers=user,
        params={"date": target_date.isoformat()},
    )
    slots_second = client.get(
        f"/rooms/{room_id}/slots/list",
        headers=user,
        params={"date": target_date.isoformat()},
    )

    assert slots_first.status_code == 200
    assert slots_second.status_code == 200

    ids_1 = [slot["id"] for slot in slots_first.json()["slots"]]
    ids_2 = [slot["id"] for slot in slots_second.json()["slots"]]

    assert len(ids_1) == 4
    assert ids_1 == ids_2


def test_slots_without_schedule_return_empty(client):
    admin = auth_headers(client, "admin")
    user = auth_headers(client, "user")

    room_id = create_room(client, admin)
    target_date = date.today() + timedelta(days=1)

    response = client.get(
        f"/rooms/{room_id}/slots/list",
        headers=user,
        params={"date": target_date.isoformat()},
    )
    assert response.status_code == 200
    assert response.json()["slots"] == []


def test_schedule_rejects_invalid_days(client):
    admin = auth_headers(client, "admin")
    room_id = create_room(client, admin)

    response = client.post(
        f"/rooms/{room_id}/schedule/create",
        headers=admin,
        json={"daysOfWeek": [8], "startTime": "09:00", "endTime": "10:00"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
