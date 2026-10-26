"""A client's notifications. They are created by the workflow, never by clients."""

import logging
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.orm import Session

from bank_credit.app import schemas
from bank_credit.app.db import get_db
from bank_credit.app.deps import get_now
from bank_credit.app.errors import ApiError
from bank_credit.app.models import Client, Notification, User
from bank_credit.app.routers.auth import get_current_active_user

logger = logging.getLogger("bank_credit.routers.notification")

router = APIRouter()


def get_current_client(current_user: User = Depends(get_current_active_user)) -> Client:
    """Notifications belong to a client (clients.id), not to the login user."""
    if current_user.client is None:
        raise ApiError(
            status.HTTP_403_FORBIDDEN, "Only clients have notifications", "customers_only"
        )
    return current_user.client


def _get_own(db: Session, client: Client, notification_id: int) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.client_id == client.id
        )
    )
    if notification is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND, "Notification not found", "notification_not_found"
        )
    return notification


@router.get("/", response_model=list[schemas.NotificationRead])
def get_notifications(
    client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> list[Notification]:
    query = (
        select(Notification)
        .where(Notification.client_id == client.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    return list(db.scalars(query))


@router.get("/unread-count")
def get_unread_notifications_count(
    client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict[str, int]:
    count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.client_id == client.id, Notification.read_at.is_(None))
    )
    return {"count": count or 0}


@router.patch("/read-all")
def mark_all_notifications_as_read(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> dict[str, int]:
    result = cast(
        "CursorResult[Any]",
        db.execute(
            update(Notification)
            .where(Notification.client_id == client.id, Notification.read_at.is_(None))
            .values(read_at=now)
        ),
    )
    db.commit()
    return {"updated": result.rowcount}


@router.get("/{notification_id:int}", response_model=schemas.NotificationRead)
def get_notification(
    notification_id: int,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> Notification:
    return _get_own(db, client, notification_id)


@router.patch("/{notification_id:int}/read", response_model=schemas.NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> Notification:
    notification = _get_own(db, client, notification_id)
    if notification.read_at is None:
        notification.read_at = now
        db.commit()
    return notification


@router.delete("/{notification_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> Response:
    db.delete(_get_own(db, client, notification_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
