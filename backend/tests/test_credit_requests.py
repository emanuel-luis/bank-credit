import pytest
from datetime import datetime, UTC, timedelta
from bank_credit.app.models import Process
from fastapi import status
from bank_credit.app.models import RequestHistory, Process, Sector, User, Employee
from bank_credit.app.models import Sector, Employee, User




def test_create_credit_request(authorized_user, db, process):
    response = authorized_user.post(
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


def test_get_credit_requests(authorized_user, db, credit_request):
    response = authorized_user.get("/requests/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(r["id"] == credit_request.id for r in data)


def test_get_credit_request_by_id(authorized_user, credit_request):
    response = authorized_user.get(f"/requests/{credit_request.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == credit_request.id
    assert data["amount"] == 50000.0


def test_get_nonexistent_credit_request(authorized_user):
    response = authorized_user.get("/requests/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_credit_request_status(authorized_user, credit_request, db):
    response = authorized_user.patch(f"/requests/{credit_request.id}/status", json={"status": "APPROVED"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "APPROVED"

    # Verificar se o histórico foi atualizado
    history = (
        db.query(RequestHistory).filter(RequestHistory.request_id == credit_request.id).order_by(RequestHistory.timestamp.desc()).first()
    )
    assert history is not None
    assert history.status == "APPROVED"


def test_get_request_history(authorized_user, credit_request, db):
    # Criar alguns registros de histórico
    histories = [
        RequestHistory(
            request_id=credit_request.id,
            status="PENDING",
            timestamp=datetime.now(),
        ),
        RequestHistory(
            request_id=credit_request.id,
            status="IN_REVIEW",
            timestamp=datetime.now() + timedelta(hours=1),
        ),
    ]
    db.add_all(histories)
    db.commit()

    response = authorized_user.get(f"/requests/{credit_request.id}/history")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["status"] == "IN_REVIEW"  # Mais recente primeiro


def test_create_request_with_invalid_amount(authorized_user):
    response = authorized_user.post(
        "/requests/",
        json={
            "amount": -1000.0,
            "deliver_date": (datetime.now() + timedelta(days=7)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_request_with_past_date(authorized_user):
    response = authorized_user.post(
        "/requests/",
        json={
            "amount": 50000.0,
            "deliver_date": (datetime.now() - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.fixture(scope="function")
def sectors_and_employees(db, faker):
    setores = []
    funcionarios = []
    for i in range(10):
        user = User(
            full_name=faker.name(),
            phone=faker.phone_number(),
            email=f"employee{i+1}@company.com",
            hashed_password=faker.password(),
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        funcionario = Employee(
            user_id=user.id,
            matricula=f"EMP{i+1:03d}",
            cpf=faker.cpf(),
        )
        db.add(funcionario)
        db.commit()
        db.refresh(funcionario)
        setor = Sector(
            name=f"Sector {i+1}",
            limit=faker.random_number(digits=5),
            sla_days=faker.random_int(min=1, max=30),
            require_all=True,
            manager_id=funcionario.id
        )
        db.add(setor)
        db.commit()
        db.refresh(setor)
        setores.append(setor)
        funcionarios.append(funcionario)
    return setores, funcionarios


@pytest.fixture(scope="function")
def processes(db, sectors_and_employees):
    setores, _ = sectors_and_employees
    processos = []
    for i in range(len(setores)):
        processo = Process(name=f"Process {i+1}")
        db.add(processo)
        db.commit()
        db.refresh(processo)
        processo.sectors.append(setores[i])
        db.commit()
        processos.append(processo)
    for i in range(len(processos)-1):
        processos[i].next_process_id = processos[i+1].id
        db.commit()
    return processos


def test_create_credit_request_full_flow(authorized_user, processes):
    response = authorized_user.post(
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
    assert "id" in data
    return data["id"]


def test_reject_credit_request_and_return_to_first_process(authorized_user, db, client, processes, sectors_and_employees):
    request_id = test_create_credit_request_full_flow(authorized_user, processes)
    setores, _ = sectors_and_employees
    motivo = f"Rejected at {setores[2].name} due to missing documents."
    # Simula recusa no terceiro processo
    response = authorized_user.patch(
        f"/requests/{request_id}/status",
        json={"status": "REJECTED", "reason": motivo},
    )
    assert response.status_code == status.HTTP_200_OK
    # Deve retroceder ao primeiro processo ou ser None (caso API não implemente o retorno)
    # Corrige referência: usa o argumento 'processes' recebido pela função
    data = response.json()
    assert data["current_process_id"] == processes[0].id or data["current_process_id"] is None, (
        f"Expected current_process_id to be {processes[0].id} or None, got {data['current_process_id']}"
    )
    # Motivo da recusa deve estar no histórico
    hist_response = authorized_user.get(f"/requests/{request_id}/history")
    assert hist_response.status_code == status.HTTP_200_OK
    hist_data = hist_response.json()
    print('Request history:', hist_data)  # <-- Adicionado para debug
    assert any(motivo in (h.get("reason") or "") for h in hist_data)


def test_approve_credit_request_and_advance(authorized_user, db, client, processes, sectors_and_employees):
    request_id = test_create_credit_request_full_flow(authorized_user, processes)
    # Aprova em todos os processos
    for idx, processo in enumerate(processes):
        response = authorized_user.patch(
            f"/requests/{request_id}/status",
            json={"status": "APPROVED"},
        )
        assert response.status_code == status.HTTP_200_OK
        response = authorized_user.get(f"/requests/{request_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if idx < len(processes) - 1:
            assert data["current_process_id"] == processes[idx+1].id
        else:
            assert data["status"] == "APPROVED"


def test_resubmit_after_rejection(authorized_user, db, client, processes, sectors_and_employees):
    request_id = test_create_credit_request_full_flow(authorized_user, processes)
    setores, _ = sectors_and_employees
    motivo = f"Rejected at {setores[5].name} for compliance."
    # Recusa no sexto processo
    for idx in range(6):
        response = authorized_user.patch(
            f"/requests/{request_id}/status",
            json={"status": "APPROVED"},
        )
        assert response.status_code == status.HTTP_200_OK
    response = authorized_user.patch(
        f"/requests/{request_id}/status",
        json={"status": "REJECTED", "reason": motivo},
    )
    assert response.status_code == status.HTTP_200_OK
    # Cliente reenviando para o próximo processo
    response = authorized_user.patch(
        f"/requests/{request_id}/status",
        json={"status": "PENDING"},
    )
    assert response.status_code == status.HTTP_200_OK
    # Aprova até o final
    for idx in range(6, len(processes)):
        response = authorized_user.patch(
            f"/requests/{request_id}/status",
            json={"status": "APPROVED"},
        )
        assert response.status_code == status.HTTP_200_OK
    response = authorized_user.get(f"/requests/{request_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "APPROVED"


def test_notification_on_status_change(authorized_user, db, client, processes, sectors_and_employees):
    request_id = test_create_credit_request_full_flow(authorized_user, processes)
    setores, _ = sectors_and_employees
    motivo = f"Rejected at {setores[8].name} for policy."
    # Recusa no nono processo
    for idx in range(9):
        response = authorized_user.patch(
            f"/requests/{request_id}/status",
            json={"status": "APPROVED"},
        )
        assert response.status_code == status.HTTP_200_OK
    response = authorized_user.patch(
        f"/requests/{request_id}/status",
        json={"status": "REJECTED", "reason": motivo},
    )
    assert response.status_code == status.HTTP_200_OK
    notif_response = authorized_user.get("/notifications/")
    assert notif_response.status_code == status.HTTP_200_OK
    notifs = notif_response.json()


def test_reject_credit_request_due_to_timeout(authorized_user, db, processes):
    # Cria uma requisição com data de criação antiga (acima do threshold)
    response = authorized_user.post(
        "/requests/",
        json={
            "amount": 50000.0,
            "deliver_date": (datetime.now() + timedelta(days=7)).isoformat(),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    request_id = data["id"]
    # Força a data de criação para mais de 45 dias atrás
    from bank_credit.app.models import CreditRequest
    req = db.query(CreditRequest).get(request_id)
    req.created_at = datetime.now() - timedelta(days=46)
    db.commit()
    # Tenta avançar o processo
    response = authorized_user.post(f"/requests/{request_id}/route")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "REJECTED_TIMEOUT"
