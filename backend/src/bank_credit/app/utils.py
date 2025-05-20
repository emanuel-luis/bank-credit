# app/utils.py

import threading
from datetime import datetime, UTC, timedelta
import networkx as nx
from sqlalchemy.orm import Session

from bank_credit.app.database import SessionLocal
from bank_credit.app import models


def send_notification(db: Session, client_id: int, subject: str, message: str):
    """
    Cria uma nova notificação para o cliente informado.
    """
    notif = models.Notification(
        client_id=client_id,
        subject=subject,
        message=message,
        read=False,
        created_at=datetime.now(),
    )
    db.add(notif)
    db.commit()


def build_process_graph(db: Session) -> nx.DiGraph:
    """
    Constrói e retorna um grafo direcionado (networkx.DiGraph)
    a partir das definições de Processos e seus next_process_id.
    """
    close_db = False
    G = nx.DiGraph()
    processes = db.query(models.Process).all()
    for proc in processes:
        G.add_node(proc.id)
        if proc.next_process_id is not None:
            G.add_edge(proc.id, proc.next_process_id)

    if close_db:
        db.close()
    return G


def schedule_sla_alert(db: Session, request_id: int, sla_days: int):
    """
    Agenda um alerta para verificar SLA ultrapassado após `sla_days` dias.
    Será executado em background via threading.Timer.
    """

    def _alert():
        try:
            req = db.query(models.CreditRequest).get(request_id)
            if not req:
                return

            # Se ainda estiver pendente em algum setor, dispara notificação
            if req.status.startswith("PENDING_"):
                deadline = req.updated_at + timedelta(days=sla_days)
                if datetime.now() >= deadline:
                    send_notification(
                        client_id=req.client_id,
                        subject="Alerta de SLA ultrapassado",
                        message=f"Seu pedido #{request_id} ultrapassou o SLA de {sla_days} dias no setor.",
                    )
        finally:
            db.close()

    # agenda execução após sla_days dias (em segundos)
    delay = sla_days * 24 * 3600
    timer = threading.Timer(delay, _alert)
    timer.daemon = True
    timer.start()
