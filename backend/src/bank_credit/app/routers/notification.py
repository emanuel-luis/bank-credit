# app/routers/notification.py

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import not_
from sqlalchemy.orm import Session

from bank_credit.app import models, schemas
from bank_credit.app.database import get_db
from bank_credit.app.email import send_notification_email
from bank_credit.app.routers.auth import get_current_active_user
from bank_credit.app.views import auth as auth_view

logger = logging.getLogger("bank_credit.routers.notification")

router = APIRouter()


def get_current_client(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> models.Client:
    """Notifications belong to a client (clients.id), not to the login user."""
    client = auth_view.get_client_by_user_id(db, current_user.id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Apenas clientes têm notificações."
        )
    return client


@router.post("/", response_model=schemas.NotificationRead)
async def create_notification(
    notification_in: schemas.NotificationCreate,
    background_tasks: BackgroundTasks,
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[POST /notifications] User {client.id} - Creating notification: {notification_in.subject}"
    )
    try:
        notification = models.Notification(
            client_id=client.id,
            subject=notification_in.subject,
            message=notification_in.message,
            read=False,
            created_at=datetime.now(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        logger.info(f"Notification {notification.id} created for client {client.id}")
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise
    # Enviar email em background
    background_tasks.add_task(
        send_notification_email,
        client.user.email,
        notification.subject,
        notification.message,
    )

    return notification


@router.get("/", response_model=list[schemas.NotificationRead])
def get_notifications(
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(f"[GET /notifications] User {client.id}")
    try:
        notifications = (
            db.query(models.Notification)
            .filter(models.Notification.client_id == client.id)
            .order_by(models.Notification.created_at.desc())
            .all()
        )
        logger.debug(f"Found {len(notifications)} notifications for user {client.id}")
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise


@router.get("/{notification_id:int}", response_model=schemas.NotificationRead)
def get_notification(
    notification_id: int,
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[GET /notifications/{{notification_id}}] User {client.id} - Notification {notification_id}"
    )
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == client.id,
        )
        .first()
    )
    if not notification:
        logger.warning(f"Notification {notification_id} not found for user {client.id}")
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    logger.debug(f"Notification found: {notification}")
    return notification


@router.patch("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[PATCH /notifications/{{notification_id}}/read] User {client.id} - Mark as read {notification_id}"
    )
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == client.id,
        )
        .first()
    )
    if not notification:
        logger.warning(f"Notification {notification_id} not found for user {client.id}")
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    notification.read = True
    db.commit()
    db.refresh(notification)
    logger.debug(f"Notification {notification_id} marked as read")
    return notification


@router.patch("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(f"[PATCH /notifications/read-all] User {client.id} - Mark all as read")
    try:
        updated = (
            db.query(models.Notification)
            .filter(
                models.Notification.client_id == client.id,
                not_(models.Notification.read),
            )
            .update({"read": True}, synchronize_session="fetch")
        )
        db.commit()
        logger.debug(f"Marked {updated} notifications as read for user {client.id}")
        return {"message": "Todas as notificações foram marcadas como lidas"}
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise


@router.get("/unread-count")
def get_unread_notifications_count(
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(f"[GET /notifications/unread-count] User {client.id}")
    try:
        count = (
            db.query(models.Notification)
            .filter(
                models.Notification.client_id == client.id,
                not_(models.Notification.read),
            )
            .count()
        )
        logger.debug(f"User {client.id} has {count} unread notifications")
        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting unread notifications count: {e}")
        raise


@router.delete("/{notification_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    client: models.Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[DELETE /notifications/{{notification_id}}] User {client.id} - Delete notification {notification_id}"
    )
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == client.id,
        )
        .first()
    )
    if not notification:
        logger.warning(f"Notification {notification_id} not found for user {client.id}")
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    db.delete(notification)
    db.commit()
    logger.info(f"Notification {notification_id} deleted for user {client.id}")
