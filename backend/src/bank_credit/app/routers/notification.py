# app/routers/notification.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, UTC


from bank_credit.app.database import get_db
from bank_credit.app.routers.auth import get_current_active_user
from bank_credit.app import models, schemas
from bank_credit.app.email import send_notification_email
from sqlalchemy import not_

router = APIRouter()


@router.post("/", response_model=schemas.NotificationRead)
async def create_notification(
    notification_in: schemas.NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification = models.Notification(
        client_id=current_user.id,
        subject=notification_in.subject,
        message=notification_in.message,
        read=False,
        created_at=datetime.now(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Enviar email em background
    background_tasks.add_task(
        send_notification_email,
        current_user.email,
        notification.subject,
        notification.message,
    )

    return notification


@router.get("/", response_model=List[schemas.NotificationRead])
def get_notifications(
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.client_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@router.get("/{notification_id:int}", response_model=schemas.NotificationRead)
def get_notification(
    notification_id: int,
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return notification


@router.patch("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark all unread notifications as read for the current user
    """
    # Refresh current_user to ensure it's attached to the session
    db.refresh(current_user)

    # Update all unread notifications
    db.query(models.Notification).filter(
        models.Notification.client_id == current_user.id,
        not_(models.Notification.read),
    ).update({"read": True}, synchronize_session="fetch")
    db.commit()

    return {"message": "Todas as notificações foram marcadas como lidas"}


@router.get("/unread-count")
def get_unread_notifications_count(
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get the count of unread notifications for the current user
    """
    return dict(
        count=db.query(models.Notification)
        .filter(
            models.Notification.client_id == current_user.id,
            not_(models.Notification.read),
        )
        .count()
    )


@router.delete("/{notification_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: models.Client = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.client_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    db.delete(notification)
    db.commit()
    return None
