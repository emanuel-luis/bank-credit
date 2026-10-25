# Utility wrappers for endpoints (migrated from crud.py)
import logging
from datetime import timedelta

import networkx as nx
from sqlalchemy.orm import Session

from bank_credit.app import models, schemas
from bank_credit.app.utils import build_process_graph

logger = logging.getLogger("bank_credit.views.utils")


def get_process_graph_data(db: Session) -> nx.DiGraph:
    logger.debug("Obtendo grafo de processos")
    G = build_process_graph(db)
    logger.debug(f"Grafo obtido: {G}")
    return G


def get_request_status(db: Session, request_id: int) -> str | None:
    logger.debug(f"Obtendo status do pedido {request_id}")
    from .credit_request import get_credit_request

    req = get_credit_request(db, request_id)
    logger.debug(f"Status encontrado: {req.status if req else None}")
    return req.status if req else None


def get_estimated_time_to_completion(db: Session, request_id: int) -> timedelta | None:
    logger.debug(f"Estimando tempo para conclusão do pedido {request_id}")
    from .credit_request import get_credit_request

    req = get_credit_request(db, request_id)
    if not req or req.current_process_id is None:
        logger.debug("Pedido não encontrado ou já finalizado")
        return None
    G = build_process_graph(db)
    path = nx.shortest_path(G, source=req.current_process_id, target=None)  # may need custom logic
    total = timedelta()
    for pid in path:
        proc = db.query(models.Process).get(pid)
        sla = min([s.sla_days for s in proc.sectors] or [0])
        total += timedelta(days=sla)
    logger.debug(f"Tempo estimado: {total}")
    return total


def get_request_history(db: Session, request_id: int) -> list[schemas.RequestHistory]:
    logger.debug(f"Obtendo histórico do pedido {request_id}")
    from .credit_request import get_credit_request

    req = get_credit_request(db, request_id)
    if not req:
        logger.debug("Pedido não encontrado")
        return []
    history = [schemas.RequestHistory.model_validate(hist) for hist in req.history]
    logger.debug(f"Histórico encontrado: {history}")
    return history
