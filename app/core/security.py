from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import os
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import APIError

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390_000


@dataclass(slots=True)
class Principal:
    user_id: UUID
    role: str


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return (
        f"{PASSWORD_ALGORITHM}$"
        f"{PASSWORD_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode('utf-8')}$"
        f"{base64.urlsafe_b64encode(digest).decode('utf-8')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_b64, expected_b64 = password_hash.split("$", maxsplit=3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected = base64.urlsafe_b64decode(expected_b64.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_access_token(*, user_id: UUID, role: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Principal:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = UUID(payload["user_id"])
        role = payload["role"]
    except (JWTError, KeyError, ValueError) as exc:
        raise APIError(status_code=401, code="UNAUTHORIZED", message="invalid token") from exc

    if role not in {"admin", "user"}:
        raise APIError(status_code=401, code="UNAUTHORIZED", message="invalid token role")

    return Principal(user_id=user_id, role=role)
