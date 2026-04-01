from datetime import date, timedelta

from fastapi.testclient import TestClient


def auth_headers(client: TestClient, role: str) -> dict[str, str]:
    response = client.post("/dummyLogin", json={"role": role})
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def create_room(client: TestClient, admin_headers: dict[str, str], *, name: str = "Room A") -> str:
    response = client.post(
        "/rooms/create",
        headers=admin_headers,
        json={"name": name, "description": "desc", "capacity": 10},
    )
    assert response.status_code == 201
    return response.json()["room"]["id"]


def create_schedule(
    client: TestClient,
    admin_headers: dict[str, str],
    room_id: str,
    *,
    day_of_week: int,
    start: str = "09:00",
    end: str = "10:00",
) -> None:
    response = client.post(
        f"/rooms/{room_id}/schedule/create",
        headers=admin_headers,
        json={
            "daysOfWeek": [day_of_week],
            "startTime": start,
            "endTime": end,
        },
    )
    assert response.status_code == 201


def next_date_for_weekday(day_of_week: int) -> date:
    today = date.today()
    delta = (day_of_week - today.isoweekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def prepare_bookable_slot(client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str]) -> tuple[str, str]:
    room_id = create_room(client, admin_headers, name="Bookable Room")

    target_date = date.today() + timedelta(days=1)
    day_of_week = target_date.isoweekday()
    create_schedule(client, admin_headers, room_id, day_of_week=day_of_week, start="09:00", end="10:00")

    slots_response = client.get(
        f"/rooms/{room_id}/slots/list",
        headers=user_headers,
        params={"date": target_date.isoformat()},
    )
    assert slots_response.status_code == 200
    slots = slots_response.json()["slots"]
    assert len(slots) >= 1

    return slots[0]["id"], target_date.isoformat()
