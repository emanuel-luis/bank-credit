"""Authentication, client registration and the current-user dependencies."""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_credit.app import schemas
from bank_credit.app.db import get_db
from bank_credit.app.deps import get_now
from bank_credit.app.domain.enums import UserRole
from bank_credit.app.email import send_welcome_email
from bank_credit.app.errors import ApiError
from bank_credit.app.models import Client, User
from bank_credit.app.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
router = APIRouter()
logger = logging.getLogger("bank_credit.routers.auth")


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    email = decode_access_token(token)
    user = get_user_by_email(db, email) if email else None
    if user is None:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "Could not validate credentials",
            "invalid_credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise ApiError(status.HTTP_400_BAD_REQUEST, "Inactive user", "inactive_user")
    return current_user


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> dict[str, str]:
    user = get_user_by_email(db, form_data.username)
    if (
        user is None
        or not user.is_active
        or not verify_password(form_data.password, user.hashed_password)
    ):
        logger.warning("Login failed for %s", form_data.username)
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            "invalid_login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login_at = now
    db.commit()
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}


@router.post("/register/client", response_model=schemas.ClientWithUser)
def register_client(
    body: schemas.ClientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> Client:
    if db.scalar(select(Client.id).where(Client.cnpj == body.cnpj)):
        raise ApiError(status.HTTP_400_BAD_REQUEST, "CNPJ already registered", "cnpj_taken")
    if get_user_by_email(db, body.user.email):
        raise ApiError(status.HTTP_400_BAD_REQUEST, "Email already registered", "email_taken")
    user = User(
        email=body.user.email,
        full_name=body.user.full_name,
        phone=body.user.phone,
        hashed_password=get_password_hash(body.user.password),
        role=UserRole.CUSTOMER,
        created_at=now,
    )
    client = Client(user=user, **body.model_dump(exclude={"user"}))
    db.add(client)
    db.commit()
    logger.info("Registered client %s (user %s)", client.id, user.id)
    background_tasks.add_task(send_welcome_email, user.email, user.full_name)
    return client


@router.get("/me", response_model=schemas.Me)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
