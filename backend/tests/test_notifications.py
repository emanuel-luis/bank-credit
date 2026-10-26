import pytest
from conftest import T0
from fastapi import status
from sqlalchemy import select

from bank_credit.app.models import Notification


@pytest.fixture
def notification(db, customer):
    row = Notification(
        client_id=customer.client.id, subject="Subject", message="Message", created_at=T0
    )
    db.add(row)
    db.commit()
    return row


def test_clients_cannot_create_notifications(test_app, auth, customer):
    response = test_app.post(
        "/notifications/", json={"subject": "x", "message": "y"}, headers=auth(customer)
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_list_and_get(test_app, auth, customer, notification):
    listing = test_app.get("/notifications/", headers=auth(customer))
    assert listing.status_code == status.HTTP_200_OK
    assert [n["id"] for n in listing.json()] == [notification.id]
    assert listing.json()[0]["read_at"] is None
    one = test_app.get(f"/notifications/{notification.id}", headers=auth(customer))
    assert one.json()["subject"] == "Subject"


def test_get_nonexistent(test_app, auth, customer):
    response = test_app.get("/notifications/999", headers=auth(customer))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "notification_not_found"


def test_other_clients_notifications_are_hidden(test_app, auth, other_customer, notification):
    assert (
        test_app.get(f"/notifications/{notification.id}", headers=auth(other_customer)).status_code
        == 404
    )
    assert (
        test_app.delete(
            f"/notifications/{notification.id}", headers=auth(other_customer)
        ).status_code
        == 404
    )
    assert test_app.get("/notifications/", headers=auth(other_customer)).json() == []


def test_staff_have_no_notifications(test_app, auth, retail_staff):
    assert test_app.get("/notifications/", headers=auth(retail_staff)).status_code == 403


def test_mark_as_read(test_app, auth, db, clock, customer, notification):
    response = test_app.patch(f"/notifications/{notification.id}/read", headers=auth(customer))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["read_at"] == "2026-01-05T10:00:00Z"
    db.refresh(notification)
    assert notification.read_at == clock.now


def test_mark_all_and_unread_count(test_app, auth, db, customer):
    db.add_all(
        Notification(client_id=customer.client.id, subject=f"s{i}", message="m", created_at=T0)
        for i in range(3)
    )
    db.commit()
    assert test_app.get("/notifications/unread-count", headers=auth(customer)).json() == {
        "count": 3
    }
    response = test_app.patch("/notifications/read-all", headers=auth(customer))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"updated": 3}
    assert test_app.get("/notifications/unread-count", headers=auth(customer)).json() == {
        "count": 0
    }
    assert all(n.read_at == T0 for n in db.scalars(select(Notification)))


def test_delete(test_app, auth, db, customer, notification):
    response = test_app.delete(f"/notifications/{notification.id}", headers=auth(customer))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert db.get(Notification, notification.id) is None
    assert test_app.delete("/notifications/999", headers=auth(customer)).status_code == 404
