import pytest
from datetime import datetime, UTC, timedelta
from fastapi import status
from bank_credit.app.models import CreditRequest, RequestHistory, Process, Sector


@pytest.fixture
def test_process(db):
    process = Process(name="Test Process")
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


@pytest.fixture
def test_sector(db):
    sector = Sector(name="Test Sector", limit=100000.0, sla_days=2, require_all=True)
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return sector


@pytest.fixture
def test_credit_request(db, test_user, test_process):
    credit_request = CreditRequest(
        client_id=test_user.id,
        amount=50000.0,
        status="PENDING",
        created_at=datetime.now(),
        deliver_date=datetime.now() + timedelta(days=7),
        current_process_id=test_process.id,
    )
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
    return credit_request


def test_create_credit_request(authorized_client, test_process):
    response = authorized_client.post(
        "/requests/",
        json={
            "amount": 50000.0,
            "deliver_date": (datetime.now() + timedelta(days=7)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == 50000.0
    assert data["status"] == "PENDING"


def test_get_credit_requests(authorized_client, test_credit_request):
    response = authorized_client.get("/requests/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == test_credit_request.id


def test_get_credit_request_by_id(authorized_client, test_credit_request):
    response = authorized_client.get(f"/requests/{test_credit_request.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_credit_request.id
    assert data["amount"] == 50000.0


def test_get_nonexistent_credit_request(authorized_client):
    response = authorized_client.get("/requests/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_credit_request_status(authorized_client, test_credit_request, db):
    response = authorized_client.patch(f"/requests/{test_credit_request.id}/status", json={"status": "APPROVED"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "APPROVED"

    # Verificar se o histórico foi atualizado
    history = (
        db.query(RequestHistory).filter(RequestHistory.request_id == test_credit_request.id).order_by(RequestHistory.timestamp.desc()).first()
    )
    assert history is not None
    assert history.status == "APPROVED"


def test_get_request_history(authorized_client, test_credit_request, db):
    # Criar alguns registros de histórico
    histories = [
        RequestHistory(
            request_id=test_credit_request.id,
            status="PENDING",
            timestamp=datetime.now(),
        ),
        RequestHistory(
            request_id=test_credit_request.id,
            status="IN_REVIEW",
            timestamp=datetime.now() + timedelta(hours=1),
        ),
    ]
    db.add_all(histories)
    db.commit()

    response = authorized_client.get(f"/requests/{test_credit_request.id}/history")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["status"] == "IN_REVIEW"  # Mais recente primeiro


def test_create_request_with_invalid_amount(authorized_client):
    response = authorized_client.post(
        "/requests/",
        json={
            "amount": -1000.0,
            "deliver_date": (datetime.now() + timedelta(days=7)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_request_with_past_date(authorized_client):
    response = authorized_client.post(
        "/requests/",
        json={
            "amount": 50000.0,
            "deliver_date": (datetime.now() - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
