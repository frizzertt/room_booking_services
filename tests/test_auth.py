from jose import jwt

from app.core.config import settings


def test_dummy_login_contains_fixed_user_id(client):
    response = client.post("/dummyLogin", json={"role": "admin"})
    assert response.status_code == 200

    token = response.json()["token"]
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

    assert payload["role"] == "admin"
    assert payload["user_id"] == settings.admin_dummy_user_id


def test_dummy_login_rejects_invalid_role(client):
    response = client.post("/dummyLogin", json={"role": "manager"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_register_and_login(client):
    register = client.post(
        "/register",
        json={"email": "person@example.com", "password": "strong123", "role": "user"},
    )
    assert register.status_code == 201

    login = client.post("/login", json={"email": "person@example.com", "password": "strong123"})
    assert login.status_code == 200
    assert isinstance(login.json()["token"], str)


def test_login_with_wrong_password(client):
    client.post(
        "/register",
        json={"email": "person2@example.com", "password": "strong123", "role": "user"},
    )

    login = client.post("/login", json={"email": "person2@example.com", "password": "bad-password"})
    assert login.status_code == 401
    assert login.json()["error"]["code"] == "UNAUTHORIZED"
