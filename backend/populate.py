from datetime import datetime, UTC, timedelta
from bank_credit.app.database import SessionLocal, engine, Base
from bank_credit.app.models import (
    Client,
    Sector,
    Process,
    CreditRequest,
    RequestHistory,
    Notification,
    User,
    Employee,
)
from bank_credit.app.routers.auth import get_password_hash
import argparse
import random
from faker import Faker
from sqlalchemy.exc import IntegrityError


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
            Client(
                username="joao.silva",
                hashed_password=get_password_hash("senha123"),
                is_active=True,
            ),
            Client(
                username="maria.santos",
                hashed_password=get_password_hash("senha456"),
                is_active=True,
            ),
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
                created_at=datetime.now(),
                deliver_date=datetime.now() + timedelta(days=7),
                current_process_id=processes[0].id,
            ),
            CreditRequest(
                client_id=clients[1].id,
                amount=150000.0,
                status="PENDING",
                created_at=datetime.now(),
                deliver_date=datetime.now() + timedelta(days=10),
                current_process_id=processes[0].id,
            ),
        ]
        db.add_all(credit_requests)
        db.commit()

        # Criar histórico para as solicitações
        histories = [
            RequestHistory(
                request_id=credit_requests[0].id,
                status="PENDING",
                timestamp=datetime.now(),
            ),
            RequestHistory(
                request_id=credit_requests[1].id,
                status="PENDING",
                timestamp=datetime.now(),
            ),
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
                created_at=datetime.now(),
            ),
            Notification(
                client_id=clients[1].id,
                subject="Documentação Necessária",
                message="Por favor, envie os documentos necessários para análise do seu crédito.",
                read=False,
                created_at=datetime.now(),
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


def populate_db(clients=200, sectors=8, processes=6, force=False, seed=None, only=None):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    fake = Faker('pt_BR')
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
    try:
        if force:
            print("Forçando repopulação: limpando todas as tabelas...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        elif db.query(Client).first():
            print("Banco de dados já possui dados. Use --force para repopular.")
            return
        # Setores e funcionários
        sector_objs = []
        employee_objs = []
        for i in range(sectors):
            sector_name = fake.unique.job()[:30]
            limit = random.randint(1000, 100000)
            sla_days = random.randint(1, 10)
            require_all = random.choice([True, False])
            # Cria funcionário gerente
            user = User(
                full_name=fake.name(),
                phone=fake.msisdn()[0:11],
                email=fake.unique.email(),
                hashed_password=get_password_hash("teste@12345"),
                is_active=True,
                is_superuser=False,
                created_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            employee = Employee(
                user_id=user.id,
                matricula=f"EMP{i+1:03d}",
                cpf=fake.cpf(),
            )
            db.add(employee)
            db.commit()
            db.refresh(employee)
            sector = Sector(
                name=sector_name,
                limit=limit,
                sla_days=sla_days,
                require_all=require_all,
                manager_id=employee.id
            )
            db.add(sector)
            db.commit()
            db.refresh(sector)
            sector_objs.append(sector)
            employee_objs.append(employee)
        # Processos (fluxo orgânico)
        process_objs = []
        for i in range(processes):
            pname = f"Processo {fake.word().capitalize()} {i+1}"
            proc = Process(name=pname)
            db.add(proc)
            db.commit()
            db.refresh(proc)
            # Associa setores aleatórios
            n_sec = random.randint(1, min(3, len(sector_objs)))
            chosen = random.sample(sector_objs, n_sec)
            proc.sectors.extend(chosen)
            db.commit()
            process_objs.append(proc)
        # Liga processos em cadeia, mas com saltos orgânicos
        for i, proc in enumerate(process_objs[:-1]):
            jump = random.randint(1, min(2, len(process_objs)-i-1))
            proc.next_process_id = process_objs[i+jump].id
            db.commit()
        # Clientes
        client_objs = []
        for i in range(clients):
            user = User(
                full_name=fake.name(),
                phone=fake.msisdn()[0:11],
                email=fake.unique.email(),
                hashed_password=get_password_hash("teste@12345"),
                is_active=True,
                is_superuser=False,
                created_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            client = Client(
                user_id=user.id,
                cnpj=fake.unique.cnpj(),
                nome_fantasia=fake.company(),
                razao_social=fake.company_suffix(),
                cnae_principal="6201-5/01",
                cnae_principal_desc="Desenvolvimento de programas de computador sob encomenda",
                natureza_juridica="2062",
                natureza_juridica_desc="Sociedade Empresária Limitada",
                logradouro=fake.street_name(),
                numero=fake.building_number(),
                cep=fake.postcode().replace("-", ""),
                bairro=fake.bairro(),
                municipio=fake.city(),
                uf=fake.estado_sigla(),
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            client_objs.append(client)
        # Solicitações de crédito orgânicas
        for client in random.sample(client_objs, min(30, len(client_objs))):
            amount = random.randint(1000, 200000)
            status = random.choice(["PENDING", "APPROVED", "REJECTED"])
            created_at = datetime.now() - timedelta(days=random.randint(0, 60))
            deliver_date = created_at + timedelta(days=random.randint(5, 30))
            process = random.choice(process_objs)
            req = CreditRequest(
                client_id=client.id,
                amount=amount,
                status=status,
                created_at=created_at,
                deliver_date=deliver_date,
                current_process_id=process.id,
            )
            db.add(req)
            db.commit()
            db.refresh(req)
            # Histórico
            hist = RequestHistory(
                request_id=req.id,
                status=status,
                timestamp=created_at,
            )
            db.add(hist)
            db.commit()
            # Notificações
            notif = Notification(
                client_id=client.id,
                subject="Solicitação de crédito",
                message=f"Sua solicitação de R$ {amount} está com status: {status}",
                read=random.choice([True, False]),
                created_at=created_at,
            )
            db.add(notif)
            db.commit()
        print(f"População concluída: {len(client_objs)} clientes, {len(sector_objs)} setores, {len(process_objs)} processos.")
    except IntegrityError as e:
        print(f"Erro de integridade: {e}")
        db.rollback()
    except Exception as e:
        print(f"Erro ao popular banco: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Popula o banco de dados do Bank Credit System.")
    parser.add_argument('--force', action='store_true', help='Força repopulação do banco (apaga tudo)')
    parser.add_argument('--seed', type=int, default=None, help='Seed para geração dos dados')
    parser.add_argument('--clients', type=int, default=200, help='Quantidade de clientes')
    parser.add_argument('--sectors', type=int, default=8, help='Quantidade de setores')
    parser.add_argument('--processes', type=int, default=6, help='Quantidade de processos')
    parser.add_argument('--only', type=str, default=None, help='Entidade única para popular (clients, sectors, processes)')
    args = parser.parse_args()
    populate_db(clients=args.clients, sectors=args.sectors, processes=args.processes, force=args.force, seed=args.seed, only=args.only)

if __name__ == "__main__":
    main()
