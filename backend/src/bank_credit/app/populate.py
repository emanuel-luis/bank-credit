from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from bank_credit.app.database import SessionLocal, engine, Base
from bank_credit.app.models import Client, Sector, Process, CreditRequest, RequestHistory, Notification
from bank_credit.app.auth import get_password_hash


def create_initial_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Verificar se já existem dados
        if db.query(Client).first():
            print("Banco de dados já possui dados iniciais.")
            return

        # Criar usuários de exemplo
        clients = [
            Client(username="joao.silva", hashed_password=get_password_hash("senha123"), is_active=True),
            Client(username="maria.santos", hashed_password=get_password_hash("senha456"), is_active=True),
        ]
        db.add_all(clients)
        db.commit()

        # Criar setores
        sectors = [
            Sector(name="Análise Inicial", limit=50000.0, sla_days=1, require_all=True),
            Sector(name="Análise de Crédito", limit=100000.0, sla_days=2, require_all=True),
            Sector(name="Análise de Risco", limit=200000.0, sla_days=3, require_all=True),
            Sector(name="Comitê Executivo", limit=500000.0, sla_days=5, require_all=True),
        ]
        db.add_all(sectors)
        db.commit()

        # Criar processos e suas relações
        processes = [
            Process(name="Verificação Inicial"),
            Process(name="Análise de Documentos"),
            Process(name="Avaliação de Crédito"),
            Process(name="Aprovação Final"),
        ]

        # Configurar a sequência dos processos
        for i in range(len(processes) - 1):
            processes[i].next_process = processes[i + 1]

        # Associar setores aos processos
        processes[0].sectors.append(sectors[0])  # Verificação Inicial -> Análise Inicial
        processes[1].sectors.extend([sectors[0], sectors[1]])  # Análise de Documentos -> Análise Inicial e de Crédito
        processes[2].sectors.extend([sectors[1], sectors[2]])  # Avaliação de Crédito -> Análise de Crédito e de Risco
        processes[3].sectors.extend([sectors[2], sectors[3]])  # Aprovação Final -> Análise de Risco e Comitê Executivo

        db.add_all(processes)
        db.commit()

        # Criar algumas solicitações de crédito de exemplo
        credit_requests = [
            CreditRequest(
                client_id=clients[0].id,
                amount=30000.0,
                status="PENDING",
                created_at=datetime.utcnow(),
                deliver_date=datetime.utcnow() + timedelta(days=7),
                current_process_id=processes[0].id,
            ),
            CreditRequest(
                client_id=clients[1].id,
                amount=150000.0,
                status="PENDING",
                created_at=datetime.utcnow(),
                deliver_date=datetime.utcnow() + timedelta(days=10),
                current_process_id=processes[0].id,
            ),
        ]
        db.add_all(credit_requests)
        db.commit()

        # Criar histórico para as solicitações
        histories = [
            RequestHistory(request_id=credit_requests[0].id, status="PENDING", timestamp=datetime.utcnow()),
            RequestHistory(request_id=credit_requests[1].id, status="PENDING", timestamp=datetime.utcnow()),
        ]
        db.add_all(histories)
        db.commit()

        # Criar algumas notificações de exemplo
        notifications = [
            Notification(
                client_id=clients[0].id,
                subject="Solicitação Recebida",
                message="Sua solicitação de crédito foi recebida e está em análise.",
                read=False,
                created_at=datetime.utcnow(),
            ),
            Notification(
                client_id=clients[1].id,
                subject="Documentação Necessária",
                message="Por favor, envie os documentos necessários para análise do seu crédito.",
                read=False,
                created_at=datetime.utcnow(),
            ),
        ]
        db.add_all(notifications)
        db.commit()

        print("Dados iniciais criados com sucesso!")

    except Exception as e:
        print(f"Erro ao criar dados iniciais: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_data()
