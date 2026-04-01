from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.serializers import user_to_dict
from app.core.config import settings
from app.core.errors import APIError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Role, User
from app.db.session import get_db

router = APIRouter(tags=["Auth"])


class DummyLoginRequest(BaseModel):
    role: str


class TokenResponse(BaseModel):
    token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def parse_role(role_raw: str) -> Role:
    try:
        return Role(role_raw)
    except ValueError as exc:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="invalid role") from exc


def ensure_dummy_user(db: Session, role: Role) -> User:
    if role == Role.admin:
        user_id = UUID(settings.admin_dummy_user_id)
        email = "dummy-admin@example.com"
    else:
        user_id = UUID(settings.user_dummy_user_id)
        email = "dummy-user@example.com"

    user = db.get(User, user_id)
    if user is not None:
        return user

    user = User(id=user_id, email=email, role=role, password_hash=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/dummyLogin", response_model=TokenResponse)
def dummy_login(payload: DummyLoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    role = parse_role(payload.role)
    user = ensure_dummy_user(db, role)
    token = create_access_token(user_id=user.id, role=user.role.value)
    return {"token": token}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, dict[str, str | None]]:
    if len(payload.password) < 6:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="password must be at least 6 chars")

    role = parse_role(payload.role)

    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise APIError(status_code=400, code="INVALID_REQUEST", message="email already exists")

    user = User(
        email=payload.email.lower(),
        role=role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": user_to_dict(user)}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or user.password_hash is None:
        raise APIError(status_code=401, code="UNAUTHORIZED", message="invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise APIError(status_code=401, code="UNAUTHORIZED", message="invalid credentials")

    return {"token": create_access_token(user_id=user.id, role=user.role.value)}
