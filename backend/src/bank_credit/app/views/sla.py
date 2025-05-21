# SLA & Overdue handling (migrated from crud.py)
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session
import logging

from bank_credit.app import models
from bank_credit.app.utils import send_notification
from .credit_request import update_request_status

logger = logging.getLogger("bank_credit.views.sla")

def check_overdue_requests(db: Session):
    logger.info("Verificando pedidos vencidos para SLA...")
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
    logger.debug(f"Pedidos vencidos encontrados: {len(overdue)}")
    for req in overdue:
        logger.info(f"Finalizando pedido {req.id} por prazo excedido")
        update_request_status(db, req, "FINALIZED")
        send_notification(
            client_id=req.client_id,
            subject="Pedido finalizado por prazo excedido",
            message="Seu pedido foi finalizado automaticamente após 20 dias sem conclusão.",
        )

def check_sla_alerts(db: Session):
    logger.info("Verificando alertas de SLA próximos do vencimento...")
    now = datetime.now()
    requests = (
        db.query(models.CreditRequest)
        .filter(
            models.CreditRequest.current_process_id.isnot(None),
            models.CreditRequest.status.like("PENDING_%"),
        )
        .all()
    )
    logger.debug(f"Pedidos em andamento: {len(requests)}")
    for req in requests:
        proc = db.query(models.Process).get(req.current_process_id)
        parts = req.status.split("_")
        sector_name = parts[-1]
        sector = db.query(models.Sector).filter(models.Sector.name == sector_name).first()
        if not sector:
            logger.warning(f"Setor {sector_name} não encontrado para pedido {req.id}")
            continue
        sla_deadline = req.updated_at + timedelta(days=sector.sla_days)
        if now + timedelta(days=1) >= sla_deadline and now < sla_deadline:
            logger.info(f"Enviando alerta de SLA para pedido {req.id} no setor {sector.name}")
            send_notification(
                client_id=req.client_id,
                subject="Alerta de SLA próximo do vencimento",
                message=f"Seu pedido #{req.id} no setor {sector.name} vencerá o SLA em breve.",
            )
