# app/routers/credit_request.py

from fastapi import APIRouter, Depends, HTTPException, status
from bank_credit.app.views import auth as auth_view
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, UTC
import logging
import os

from bank_credit.app import schemas, models
from bank_credit.app.database import get_db
from bank_credit.app.routers.auth import get_current_active_user
from bank_credit.app.views import credit_request as credit_view
from bank_credit.app.views import routing as routing_view

# Configuração global de logging
LOG_LEVEL = logging.DEBUG if os.environ.get("ENV", "dev") == "dev" else logging.INFO
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bank_credit.routers.credit_request")


def log_request_context(request_id=None, user_id=None, action=None, extra=None):
    logger.info(f"[Request {request_id}] User {user_id} - {action} - {extra if extra else ''}")


router = APIRouter()


@router.post("/", response_model=schemas.CreditRequest, status_code=status.HTTP_201_CREATED)
def create_credit_request(
    req_in: schemas.CreditRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[POST /requests] User {current_user.id} - Creating credit request")
    logger.debug(f"Request data: {req_in}")
    try:
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not client:
            logger.warning(f"User {current_user.id} is not a client")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas clientes podem criar solicitações de crédito.")
        req = credit_view.create_credit_request(db, client, req_in)
        logger.info(f"Credit request {req.id} created for client {client.id}")
        return req
    except Exception as e:
        logger.error(f"Error creating credit request: {e}")
        raise

@router.get("/", response_model=List[schemas.CreditRequest])
def list_my_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[GET /requests] User {current_user.id}")
    try:
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not client:
            logger.warning(f"User {current_user.id} is not a client")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas clientes podem listar solicitações de crédito.")
        requests = credit_view.list_client_requests(db, client.id)
        logger.debug(f"Found {len(requests)} requests for user {current_user.id}")
        return requests
    except Exception as e:
        logger.error(f"Error listing credit requests: {e}")
        raise

@router.get("/{request_id}", response_model=schemas.CreditRequest)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[GET /requests/{{request_id}}] User {current_user.id} - Request {request_id}")
    try:
        req = credit_view.get_credit_request(db, request_id)
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        logger.debug(f"Request found: {req}")
        return req
    except Exception as e:
        logger.error(f"Error fetching request {request_id}: {e}")
        raise

@router.post("/{request_id}/route", response_model=schemas.CreditRequest)
def route_request_to_next(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[POST /requests/{{request_id}}/route] User {current_user.id} - Route request {request_id}")
    try:
        req = credit_view.get_credit_request(db, request_id)
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        routed = routing_view.route_credit_request(db, req)
        logger.info(f"Request {request_id} routed to next process")
        return routed
    except Exception as e:
        logger.error(f"Error routing request {request_id}: {e}")
        raise

@router.get("/{request_id}/status", response_model=str)
def get_request_status(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[GET /requests/{{request_id}}/status] User {current_user.id} - Request {request_id}")
    try:
        req = credit_view.get_credit_request(db, request_id)
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        logger.debug(f"Request status: {req.status}")
        return req.status
    except Exception as e:
        logger.error(f"Error fetching status for request {request_id}: {e}")
        raise

@router.get("/{request_id}/estimated-time", response_model=int)
def get_estimated_time(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[GET /requests/{{request_id}}/estimated-time] User {current_user.id} - Request {request_id}")
    try:
        from datetime import timedelta
        req = credit_view.get_credit_request(db, request_id)
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        eta: timedelta = credit_view.get_estimated_time_to_completion(db, request_id)
        if eta is None:
            logger.warning(f"Estimated time unavailable for request {request_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tempo estimado indisponível",
            )
        logger.debug(f"Estimated time for request {request_id}: {eta.days} days")
        return eta.days
    except Exception as e:
        logger.error(f"Error estimating time for request {request_id}: {e}")
        raise

@router.patch("/{request_id}/status", response_model=schemas.CreditRequest)
def update_request_status(
    request_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[PATCH /requests/{{request_id}}/status] User {current_user.id} - Update status {status_update}")
    try:
        req = credit_view.get_credit_request(db, request_id)
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        status_anterior = req.status
        requested_status = status_update["status"]
        reason = status_update.get("reason")
        logger.info(f"Atualizando status do pedido {req.id} de {status_anterior} para {requested_status}")

        # --- FIXED LOGIC ---
        if requested_status == "APPROVED":
            if req.current_process and req.current_process.next_process_id:
                # Advance to next process, keep status as PENDING
                logger.debug(f"Avançando processo de {req.current_process_id} para {req.current_process.next_process_id}")
                req.current_process_id = req.current_process.next_process_id
                req.status = "PENDING"
            elif req.current_process and req.current_process.next_process_id is None:
                # Last process approved, finish request
                logger.debug(f"Finalizando processo, não há próximo processo para {req.current_process_id}")
                req.current_process_id = None
                req.status = "APPROVED"
            elif req.current_process is None:
                # Already finished, do nothing
                logger.debug(f"Pedido {req.id} já finalizado")
        elif requested_status == "REJECTED":
            # On rejection, keep process pointer, set status to REJECTED
            logger.debug(f"Pedido {req.id} rejeitado no processo {req.current_process_id}")
            req.status = "REJECTED"
        elif requested_status == "PENDING":
            # Resubmission after rejection: keep process pointer, set status to PENDING
            logger.debug(f"Pedido {req.id} reaberto para análise no processo {req.current_process_id}")
            req.status = "PENDING"
        else:
            # Any other status, set as requested
            req.status = requested_status

        db.add(req)
        db.commit()
        db.refresh(req)
        logger.debug(f"Registrando histórico: status={req.status}, reason={reason}")
        history = models.RequestHistory(request_id=req.id, status=req.status, timestamp=datetime.now(), reason=reason)
        db.add(history)
        db.commit()
        from bank_credit.app.utils import send_notification
        subject = f"Status update for request #{req.id}"  # Always contains 'status'
        message = f"The status of your credit request #{req.id} is {req.status}."
        if reason:
            message += f" Reason: {reason}"
        send_notification(client_id=req.client_id, subject=subject, message=message)
        logger.info(f"Status atualizado com sucesso para o pedido {req.id}")
        return req
    except Exception as e:
        logger.error(f"Error updating status for request {request_id}: {e}")
        raise

@router.get("/{request_id}/history", response_model=List[schemas.RequestHistory])
def get_request_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    logger.info(f"[GET /requests/{{request_id}}/history] User {current_user.id} - Request {request_id}")
    try:
        req = credit_view.get_credit_request(db, request_id)
        from bank_credit.app.views import auth as auth_view
        client = auth_view.get_client_by_user_id(db, current_user.id)
        if not req or not client or req.client_id != client.id:
            logger.warning(f"Request {request_id} not found or unauthorized for user {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
        history = (
            db.query(models.RequestHistory)
            .filter(models.RequestHistory.request_id == request_id)
            .order_by(models.RequestHistory.timestamp.desc())
            .all()
        )
        logger.debug(f"Found {len(history)} history entries for request {request_id}")
        return history
    except Exception as e:
        logger.error(f"Error fetching history for request {request_id}: {e}")
        raise
