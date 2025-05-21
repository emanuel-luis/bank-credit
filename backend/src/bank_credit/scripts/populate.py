import logging

logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, force=True, datefmt="%Y-%m-%d %H:%M:%S", format="%(asctime)s - %(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger("bank_credit.populate")

from datetime import datetime, timedelta
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
from bank_credit.app.views.auth import get_password_hash
import argparse
import random
from faker import Faker
from sqlalchemy.exc import IntegrityError

def populate_db(clients=200, sectors=8, processes=6, force=False, seed=None, only=None):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    fake = Faker('pt_BR')
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
    try:
        if force:
            logger.info("Forçando repopulação: limpando todas as tabelas...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        elif db.query(Client).first():
            logger.info("Banco de dados já possui dados. Use --force para repopular.")
            return
        # Setores e funcionários
        sector_objs = []
        employee_objs = []
        logger.info(f"Populando setores: {sectors} setor(es)")
        for i in range(sectors+1):
            logger.info(f"Populando setor {i+1}/{sectors}")
            sector_name = fake.unique.job()[:30]
            limit = random.randint(1000, 100000)
            sla_days = random.randint(1, 10)
            require_all = random.choice([True, False])
            # Cria funcionário gerente
            email = fake.unique.email()
            if i == 0:
                email = "admin@admin.com"
            user = User(
                full_name=fake.name(),
                phone=fake.msisdn()[0:11],
                email=email,
                hashed_password=get_password_hash("123"),
                is_active=True,
                is_superuser=i == 0,
                created_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            employee = Employee(
                user_id=user.id,
                matricula=f"EMP{i:03d}",
                cpf=fake.cpf(),
            )
            db.add(employee)
            db.commit()
            sector = Sector(
                name=sector_name,
                limit=limit,
                sla_days=sla_days,
                require_all=require_all,
                manager_id=employee.id
            )
            db.add(sector)
            db.commit()
            sector_objs.append(sector)
            employee_objs.append(employee)
            logger.info(f"Setor {i+1}/{sectors} adicionado: {sector}")
        # Processos (fluxo orgânico)
        process_objs = []
        logger.info(f"Populando processos: {processes} processo(s)")
        for i in range(processes):
            logger.info(f"Populando processo {i+1}/{processes}")
            pname = f"Processo {fake.word().capitalize()} {i+1}"
            proc = Process(name=pname)
            db.add(proc)
            db.commit()
            # Associa setores aleatórios
            n_sec = random.randint(1, min(3, len(sector_objs)))
            chosen = random.sample(sector_objs, n_sec)
            proc.sectors.extend(chosen)
            db.commit()
            process_objs.append(proc)
            logger.info(f"Processo {i+1}/{processes} adicionado")
        # Liga processos em cadeia, mas com saltos orgânicos
        logger.info("Conectando processos em cadeia")
        for i, proc in enumerate(process_objs[:-1]):
            logger.info(f"Conectando processo {proc.name} com o próximo")
            jump = random.randint(1, min(2, len(process_objs)-i-1))
            proc.next_process_id = process_objs[i+jump].id
            db.commit()
            logger.info(f"Processo {proc.name} conectado com {process_objs[i+jump].name}")
        # Clientes
        client_objs = []
        logger.info(f"Populando clientes: {clients} cliente(s)")
        for i in range(clients):
            logger.info(f"Populando cliente {i+1}/{clients}")
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
            client_objs.append(client)
            logger.info(f"Cliente {i+1}/{clients} adicionado")
        # Solicitações de crédito orgânicas
        for client in random.sample(client_objs, min(30, len(client_objs))):
            logger.info(f"Populando solicitação de crédito para cliente {client.nome_fantasia}")
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
            logger.info(f"Solicitação de crédito {req.id} e status {req.status} adicionada para cliente {client.nome_fantasia}")
        logger.info(f"População concluída: {len(client_objs)} clientes, {len(sector_objs)} setores, {len(process_objs)} processos.")
    except IntegrityError as e:
        logger.info(f"Erro de integridade: {e}")
        db.rollback()
    except Exception as e:
        logger.info(f"Erro ao popular banco: {e}")
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
