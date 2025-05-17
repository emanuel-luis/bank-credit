# app/routers/credit_request.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from bank_credit.app import crud, schemas, models
from bank_credit.app.database import get_db
from bank_credit.app.routers.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=schemas.CreditRequest, status_code=status.HTTP_201_CREATED)
def create_credit_request(
    req_in: schemas.CreditRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Cria uma nova solicitação de crédito.
    Faz validação inicial do checklist e retorna o pedido com status adequado.
    """
    return crud.create_credit_request(db, current_user, req_in)


@router.get("/", response_model=List[schemas.CreditRequest])
def list_my_requests(
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Lista todas as solicitações do cliente autenticado.
    """
    return crud.list_client_requests(db, current_user.id)


@router.get("/{request_id}", response_model=schemas.CreditRequest)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Recupera os detalhes completos de uma solicitação específica.
    """
    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return req


@router.post("/{request_id}/route", response_model=schemas.CreditRequest)
def route_request_to_next(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Encaminha a solicitação para o próximo processo/sector de acordo com o grafo.
    """
    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return crud.route_credit_request(db, req)


@router.get("/{request_id}/status", response_model=str)
def get_request_status(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Retorna o status atual da solicitação.
    """
    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return req.status


@router.get("/{request_id}/estimated-time", response_model=int)
def get_estimated_time(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Estima em dias o tempo restante até a finalização, somando SLAs dos processos restantes.
    """
    from datetime import timedelta

    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

    eta: timedelta = crud.get_estimated_time_to_completion(db, request_id)
    if eta is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tempo estimado indisponível",
        )

    return eta.days


@router.patch("/{request_id}/status", response_model=schemas.CreditRequest)
def update_request_status(
    request_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Atualiza o status de uma solicitação de crédito.
    """
    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

    req.status = status_update["status"]
    db.add(req)
    db.commit()
    db.refresh(req)

    # Create history entry
    history = models.RequestHistory(request_id=req.id, status=req.status, timestamp=datetime.utcnow())
    db.add(history)
    db.commit()

    return req


@router.get("/{request_id}/history", response_model=List[schemas.RequestHistory])
def get_request_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Retorna o histórico de status de uma solicitação.
    """
    req = crud.get_credit_request(db, request_id)
    if not req or req.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

    history = (
        db.query(models.RequestHistory)
        .filter(models.RequestHistory.request_id == request_id)
        .order_by(models.RequestHistory.timestamp.desc())
        .all()
    )

    return history
