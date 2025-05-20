import pytest
from datetime import datetime, UTC
from fastapi import status
from bank_credit.app.models import Notification, User, Client, Employee
from sqlalchemy import not_


@pytest.fixture
def test_notification(db, client):
    notification = Notification(
        client_id=client.id,
        subject="Test Notification",
        message="This is a test notification",
        read=False,
        created_at=datetime.now(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@pytest.fixture
def test_notification_client(db, test_client_user):
    notification = Notification(
        client_id=test_client_user.id,
        subject="Test Notification",
        message="This is a test notification",
        read=False,
        created_at=datetime.now(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@pytest.fixture
def test_notification_employee(db, test_employee_user):
    notification = Notification(
        client_id=None,  # Ajuste conforme modelo se necessário
        subject="Test Notification",
        message="This is a test notification for employee",
        read=False,
        created_at=datetime.now(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def test_create_notification(authorized_user, db):
    response = authorized_user.post(
        "/notifications/",
        json={
            "subject": "New Test Notification",
            "message": "This is a test notification with email",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["subject"] == "New Test Notification"
    assert data["message"] == "This is a test notification with email"
    assert not data["read"]
    # O email será "enviado" em background no ambiente de teste


def test_get_notifications(authorized_user, db, test_notification):
    response = authorized_user.get("/notifications/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(n["subject"] == "Test Notification" for n in data)


def test_get_notification_by_id(authorized_user, db, test_notification):
    response = authorized_user.get(f"/notifications/{test_notification.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_notification.id
    assert data["subject"] == "Test Notification"


def test_get_nonexistent_notification(authorized_user):
    response = authorized_user.get("/notifications/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_mark_notification_as_read(authorized_user, test_notification, db):
    response = authorized_user.patch(f"/notifications/{test_notification.id}/read")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["read"] is True

    # Verificar no banco de dados
    db_notification = db.query(Notification).filter(Notification.id == test_notification.id).first()
    assert db_notification.read is True


def test_mark_all_notifications_as_read(authorized_user, db, client):
    # Refresh test_user to ensure it's attached to the session
    db.refresh(client)

    # Create multiple notifications
    notifications = [
        Notification(
            client_id=client.id,
            subject=f"Test Notification {i}",
            message=f"This is test notification {i}",
            read=False,
            created_at=datetime.now(),
        )
        for i in range(3)
    ]
    db.add_all(notifications)
    db.commit()
    response = authorized_user.patch("/notifications/read-all")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Todas as notificações foram marcadas como lidas"

    # Verify all notifications are marked as read
    unread_count = db.query(Notification).filter(Notification.client_id == client.id, not_(Notification.read)).count()
    assert unread_count == 0

    # Verify all notifications exist and are marked as read
    all_notifications = db.query(Notification).filter(Notification.client_id == client.id).all()
    assert len(all_notifications) == 3
    assert all(n.read for n in all_notifications)


def test_get_unread_notifications_count(authorized_user, db, client):
    # Create notifications with alternating read status
    notifications = [
        Notification(
            client_id=client.id,
            subject=f"Test Notification {i}",
            message=f"This is test notification {i}",
            read=i % 2 == 0,  # Alternate between read and unread
            created_at=datetime.now(),
        )
        for i in range(4)
    ]
    db.add_all(notifications)
    db.commit()

    response = authorized_user.get("/notifications/unread-count")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2  # Half of the notifications are unread

    # Verify in database
    unread_count = db.query(Notification).filter(Notification.client_id == client.id, not_(Notification.read)).count()
    assert unread_count == 2


def test_delete_notification(authorized_user, test_notification, db):
    response = authorized_user.delete(f"/notifications/{test_notification.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar se a notificação foi realmente deletada
    db_notification = db.query(Notification).filter(Notification.id == test_notification.id).first()
    assert db_notification is None


def test_delete_nonexistent_notification(authorized_user):
    response = authorized_user.delete("/notifications/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
