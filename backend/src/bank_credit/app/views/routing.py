# Routing / Graph-based process flow (migrated from crud.py)
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from bank_credit.app import models, utils
from .credit_request import update_request_status
import logging

logger = logging.getLogger("bank_credit.views.routing")

THRESHOLD_CREDIT_LIMIT_DAYS = timedelta(days=45)

def route_credit_request(db: Session, request: models.CreditRequest):
    logger.info(f"Roteando pedido {request.id} (processo atual: {request.current_process_id})")
    # Recusa automática se o tempo de requisição exceder o threshold
    if datetime.now() - request.created_at >= THRESHOLD_CREDIT_LIMIT_DAYS:
        logger.warning(f"Pedido {request.id} excedeu o tempo limite de {THRESHOLD_CREDIT_LIMIT_DAYS.days} dias. Recusando automaticamente.")
        return update_request_status(db, request, "REJECTED_TIMEOUT")
    G = utils.build_process_graph(db)
    if request.current_process_id is None:
        logger.debug("Processo inicial, buscando start node")
        start_nodes = [n for n, d in G.in_degree() if d == 0]
        next_proc = db.query(models.Process).get(start_nodes[0])
    else:
        logger.debug(f"Buscando sucessores do processo {request.current_process_id}")
        successors = list(G.successors(request.current_process_id))
        if not successors:
            logger.info(f"Pedido {request.id} chegou ao final do fluxo")
            return update_request_status(db, request, "FINALIZED")
        next_proc = db.query(models.Process).get(successors[0])
    sectors = next_proc.sectors
    # Agora o limite é o valor mínimo necessário
    eligible_sectors = [s for s in sectors if request.amount >= s.limit]
    logger.debug(f"Setores elegíveis: {eligible_sectors}")
    if not eligible_sectors:
        logger.warning(f"Nenhum setor elegível para o pedido {request.id}")
        return update_request_status(db, request, "REJECTED_NO_SECTOR")
    target_sector = eligible_sectors[0]
    logger.info(f"Avançando pedido {request.id} para processo {next_proc.id} e setor {target_sector.name}")
    request.current_process_id = next_proc.id
    request.status = f"PENDING_{next_proc.name.upper()}_{target_sector.name.upper()}"
    request.updated_at = datetime.now()
    db.add(request)
    db.commit()
    from .credit_request import record_history
    record_history(db, request, request.status)
    utils.schedule_sla_alert(request.id, target_sector.sla_days)
    logger.info(f"Pedido {request.id} roteado com sucesso")
    return request
