import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, datetime, timedelta

from faker import Faker
from bank_credit.app.database import Base, get_db
from bank_credit.app.main import app
from bank_credit.app.routers.auth import create_access_token
from bank_credit.app.models import CreditRequest, Process, Sector, User, Client, Employee
from bank_credit.app.routers.auth import get_password_hash

# Configurar ambiente de teste
os.environ["TESTING"] = "true"


# Configuração do banco de dados de teste
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_app(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db, faker):
    user = User(
        full_name=faker.name(),
        phone=faker.msisdn()[0:11],
        email=faker.unique.email(),
        hashed_password=get_password_hash("test_password"),
        is_active=True,
        is_superuser=False,
        created_at=date.today(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    client = Client(
        user_id=user.id,
        cnpj=faker.unique.cnpj(),
        nome_fantasia=faker.company(),
        razao_social=faker.company_suffix(),
        cnae_principal="6201-5/01",
        cnae_principal_desc="Desenvolvimento de programas de computador sob encomenda",
        natureza_juridica="2062",
        natureza_juridica_desc="Sociedade Empresária Limitada",
        logradouro=faker.street_name(),
        numero=faker.building_number(),
        cep=faker.postcode().replace("-", ""),
        bairro=faker.bairro(),
        municipio=faker.city(),
        uf=faker.estado_sigla(),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture(scope="function")
def bearer_token(client):
    return create_access_token(data={"sub": client.user.email})


@pytest.fixture(scope="function")
def authorized_user(test_app, bearer_token):
    test_app.headers = {**test_app.headers, "Authorization": f"Bearer {bearer_token}"}
    return test_app


@pytest.fixture(scope="function")
def faker():
    return Faker("pt_BR")


@pytest.fixture(scope="function")
def employee(db):
    user = User(
        full_name="Funcionario Teste",
        phone="11987654321",
        email="funcionario@empresa.com.br",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    employee = Employee(
        user_id=user.id,
        matricula="EMP001",
        cpf="12345678901",
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture(scope="function")
def process(db):
    """
    Ensure at least one initial Process exists for tests that require it.
    """
    process = Process(name="Initial Process")
    db.add(process)
    db.commit()
    db.refresh(process)
    return process

@pytest.fixture(scope="function")
def sector(db):
    sector = Sector(name="Test Sector", limit=100000.0, sla_days=2, require_all=True)
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return sector



@pytest.fixture(scope="function")
def credit_request(db, client, process):
    credit_request = CreditRequest(
        client_id=client.id,
        amount=50000.0,
        status="PENDING",
        created_at=datetime.now(),
        deliver_date=datetime.now() + timedelta(days=7),
        current_process_id=process.id,
    )
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
    return credit_request
