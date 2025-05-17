# app/crud.py

from datetime import datetime, date, timedelta
from typing import List, Optional

import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from bank_credit.app import models, schemas, utils
from bank_credit.app.utils import send_notification, build_process_graph

# --- Client / Auth CRUD ---


def get_client_by_email(db: Session, email: str) -> Optional[models.Client]:
    """
    Busca um cliente pelo email
    """
    return db.query(models.Client).filter(models.Client.email == email).first()


def create_client(db: Session, client_in: schemas.ClientCreate) -> models.Client:
    from bank_credit.app.routers.auth import get_password_hash

    hashed_pw = get_password_hash(client_in.password)
    db_client = models.Client(
        cnpj=str(client_in.cnpj),
        full_name=str(client_in.full_name),
        birth_date=client_in.birth_date,
        phone=str(client_in.phone),
        email=str(client_in.email),
        hashed_password=hashed_pw,
        is_active=True,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


# --- Credit Request CRUD ---


def get_credit_request(db: Session, request_id: int) -> Optional[models.CreditRequest]:
    return db.query(models.CreditRequest).filter(models.CreditRequest.id == request_id).first()


def list_credit_requests(db: Session, skip: int = 0, limit: int = 100) -> List[models.CreditRequest]:
    return db.query(models.CreditRequest).offset(skip).limit(limit).all()


def list_client_requests(db: Session, client_id: int) -> List[models.CreditRequest]:
    return db.query(models.CreditRequest).filter(models.CreditRequest.client_id == client_id).all()


def record_history(db: Session, request: models.CreditRequest, status: str):
    hist = models.RequestHistory(request_id=request.id, status=status, timestamp=datetime.now())
    db.add(hist)
    db.commit()


def create_credit_request(db: Session, client: models.Client, req_in: schemas.CreditRequestCreate) -> models.CreditRequest:
    # initial checklist validation
    if not hasattr(req_in, "checklist") or not req_in.checklist:
        status = "PENDING"
    else:
        missing = [item for item in req_in.checklist if not item]
        if missing:
            # send back to client for missing docs
            send_notification(
                client_id=client.id,
                subject="Pendências na documentação",
                message=f"Documentos pendentes: {missing}",
            )
            status = "PENDING_DOCS"
        else:
            status = "CHECKLIST_OK"

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

    record_history(db, db_req, status)
    return db_req


def update_request_status(db: Session, request: models.CreditRequest, new_status: str) -> models.CreditRequest:
    request.status = new_status
    request.updated_at = datetime.now()
    db.add(request)
    db.commit()
    record_history(db, request, new_status)
    db.refresh(request)
    return request


# --- Routing / Graph-based process flow ---


def route_credit_request(db: Session, request: models.CreditRequest):
    """
    Determine next process/sector for this request based on amount and graph definitions.
    """
    # build directed graph where nodes=process IDs, edges defined by Process.next_process_id
    G = build_process_graph(db)

    # if first routing after checklist
    if request.current_process_id is None:
        # pick the first process(s) in graph: nodes with in_degree=0
        start_nodes = [n for n, d in G.in_degree() if d == 0]
        # choose smallest ID or business rule
        next_proc = db.query(models.Process).get(start_nodes[0])
    else:
        # follow the edge to next process
        successors = list(G.successors(request.current_process_id))
        if not successors:
            # end of graph: finalize
            return update_request_status(db, request, "FINALIZED")
        next_proc = db.query(models.Process).get(successors[0])

    # check which sectors must approve this process
    sectors = next_proc.sectors
    # filter sectors by limit >= request.amount
    eligible_sectors = [s for s in sectors if s.limit >= request.amount]

    if not eligible_sectors:
        # no sector can handle: escalate or finalize as rejected
        return update_request_status(db, request, "REJECTED_NO_SECTOR")

    # assign to the first eligible sector (round-robin or load-balance can replace this)
    target_sector = eligible_sectors[0]
    request.current_process_id = next_proc.id
    request.status = f"PENDING_{next_proc.name.upper()}_{target_sector.name.upper()}"
    request.updated_at = datetime.now()
    db.add(request)
    db.commit()
    record_history(db, request, request.status)

    # schedule SLA alert
    utils.schedule_sla_alert(request.id, target_sector.sla_days)

    return request


# --- SLA & Overdue handling ---


def check_overdue_requests(db: Session):
    """
    Find all requests older than 20 days in non-final status and finalize them.
    """
    cutoff = datetime.now() - timedelta(days=20)
    overdue = (
        db.query(models.CreditRequest)
        .filter(
            and_(
                models.CreditRequest.created_at < cutoff,
                models.CreditRequest.status.notin_(["FINALIZED", "REJECTED_NO_SECTOR"]),
            )
        )
        .all()
    )
    for req in overdue:
        update_request_status(db, req, "FINALIZED")
        send_notification(
            client_id=req.client_id,
            subject="Pedido finalizado por prazo excedido",
            message="Seu pedido foi finalizado automaticamente após 20 dias sem conclusão.",
        )


def check_sla_alerts(db: Session):
    """
    Scan for requests approaching SLA deadlines and send alerts.
    """
    now = datetime.now()
    # join CreditRequest.current_process_id with Process.sectors to get sla_days
    requests = (
        db.query(models.CreditRequest)
        .filter(
            models.CreditRequest.current_process_id.isnot(None),
            models.CreditRequest.status.like("PENDING_%"),
        )
        .all()
    )
    for req in requests:
        _ = db.query(models.Process).get(req.current_process_id)
        # find sector handling it via status naming convention
        parts = req.status.split("_")
        sector_name = parts[-1]
        sector = db.query(models.Sector).filter(models.Sector.name == sector_name).first()
        if not sector:
            continue
        sla_deadline = req.updated_at + timedelta(days=sector.sla_days)
        if now + timedelta(days=1) >= sla_deadline and now < sla_deadline:
            # send alert 1 day before SLA breach
            send_notification(
                client_id=req.client_id,
                subject="Alerta de SLA próximo do vencimento",
                message=f"Seu pedido #{req.id} no setor {sector.name} vencerá o SLA em breve.",
            )


# --- Utility wrappers for endpoints ---


def get_process_graph_data(db: Session) -> nx.DiGraph:
    return build_process_graph(db)


def get_request_status(db: Session, request_id: int) -> Optional[str]:
    req = get_credit_request(db, request_id)
    return req.status if req else None


def get_estimated_time_to_completion(db: Session, request_id: int) -> Optional[timedelta]:
    req = get_credit_request(db, request_id)
    if not req or req.current_process_id is None:
        return None
    # sum remaining SLA days on path to end
    G = build_process_graph(db)
    path = nx.shortest_path(G, source=req.current_process_id, target=None)  # may need custom logic
    total = timedelta()
    for pid in path:
        proc = db.query(models.Process).get(pid)
        # pick min sla_days among its sectors
        sla = min([s.sla_days for s in proc.sectors] or [0])
        total += timedelta(days=sla)
    return total


def get_request_history(db: Session, request_id: int) -> List[schemas.RequestHistory]:
    req = get_credit_request(db, request_id)
    if not req:
        return []
    return [schemas.RequestHistory.model_validate(hist) for hist in req.history]
