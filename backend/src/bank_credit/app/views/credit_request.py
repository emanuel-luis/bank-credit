# Credit request-related CRUD logic (migrated from crud.py)
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from bank_credit.app import models, schemas, utils
from bank_credit.app.utils import send_notification, build_process_graph
import logging

logger = logging.getLogger("bank_credit.views.credit_request")

def get_credit_request(db: Session, request_id: int) -> Optional[models.CreditRequest]:
    logger.info(f"[get_credit_request] Buscando pedido de crédito {request_id}")
    logger.debug(f"[get_credit_request] Parâmetros: request_id={request_id}")
    req = db.query(models.CreditRequest).filter(models.CreditRequest.id == request_id).first()
    logger.debug(f"[get_credit_request] Resultado: {req}")
    return req

def list_credit_requests(db: Session, skip: int = 0, limit: int = 100) -> List[models.CreditRequest]:
    logger.info(f"[list_credit_requests] Listando pedidos de crédito")
    logger.debug(f"[list_credit_requests] Parâmetros: skip={skip}, limit={limit}")
    result = db.query(models.CreditRequest).offset(skip).limit(limit).all()
    logger.debug(f"[list_credit_requests] Encontrados {len(result)} pedidos")
    return result

def list_client_requests(db: Session, client_id: int) -> List[models.CreditRequest]:
    logger.info(f"[list_client_requests] Listando pedidos do cliente {client_id}")
    logger.debug(f"[list_client_requests] Parâmetros: client_id={client_id}")
    result = db.query(models.CreditRequest).filter(models.CreditRequest.client_id == client_id).all()
    logger.debug(f"[list_client_requests] Encontrados {len(result)} pedidos para o cliente {client_id}")
    return result

def record_history(db: Session, request: models.CreditRequest, status: str):
    logger.info(f"[record_history] Registrando histórico para pedido {request.id}: status={status}")
    logger.debug(f"[record_history] Parâmetros: request_id={request.id}, status={status}")
    hist = models.RequestHistory(request_id=request.id, status=status, timestamp=datetime.now())
    db.add(hist)
    db.commit()
    logger.debug(f"[record_history] Histórico registrado: {hist}")

def create_credit_request(db: Session, client: models.Client, req_in: schemas.CreditRequestCreate) -> models.CreditRequest:
    logger.info(f"[create_credit_request] Criando pedido de crédito para cliente {client.id}")
    logger.debug(f"[create_credit_request] Parâmetros: client_id={client.id}, req_in={req_in}")
    if not hasattr(req_in, "checklist") or not req_in.checklist:
        status = "PENDING"
        logger.debug(f"[create_credit_request] Checklist ausente ou vazio. Status definido como PENDING.")
    else:
        missing = [item for item in req_in.checklist if not item]
        if missing:
            logger.info(f"[create_credit_request] Documentos pendentes para cliente {client.id}: {missing}")
            send_notification(
                client_id=client.id,
                subject="Pendências na documentação",
                message=f"Documentos pendentes: {missing}",
            )
            status = "PENDING_DOCS"
            logger.debug(f"[create_credit_request] Status definido como PENDING_DOCS.")
        else:
            status = "CHECKLIST_OK"
            logger.debug(f"[create_credit_request] Checklist completo. Status definido como CHECKLIST_OK.")
    now = datetime.now()
    deliver_date = req_in.deliver_date
    db_req = models.CreditRequest(
        client_id=client.id,
        amount=float(req_in.amount),
        status=status,
        created_at=now,
        updated_at=now,
        deliver_date=deliver_date,
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    logger.info(f"[create_credit_request] Pedido de crédito {db_req.id} criado para cliente {client.id}")
    record_history(db, db_req, status)
    logger.debug(f"[create_credit_request] Pedido criado: {db_req}")
    return db_req

def update_request_status(db: Session, request: models.CreditRequest, new_status: str) -> models.CreditRequest:
    logger.info(f"[update_request_status] Atualizando status do pedido {request.id} para {new_status}")
    logger.debug(f"[update_request_status] Parâmetros: request_id={request.id}, new_status={new_status}")
    request.status = new_status
    request.updated_at = datetime.now()
    if new_status == "APPROVED" and request.current_process and request.current_process.next_process_id:
        logger.debug(f"[update_request_status] Avançando processo de {request.current_process_id} para {request.current_process.next_process_id}")
        request.current_process_id = request.current_process.next_process_id
        db.add(request)
        db.commit()
        db.refresh(request)  # Ensure relationships are up-to-date
    elif new_status == "APPROVED":
        logger.debug(f"[update_request_status] Finalizando processo, não há próximo processo para {request.current_process_id}")
        request.current_process_id = None
        db.add(request)
        db.commit()
        db.refresh(request)
    else:
        db.add(request)
        db.commit()
        db.refresh(request)
    record_history(db, request, new_status)
    logger.info(f"[update_request_status] Status atualizado para {request.status} no pedido {request.id}")
    logger.debug(f"[update_request_status] Pedido atualizado: {request}")
    return request
