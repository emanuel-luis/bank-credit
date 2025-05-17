import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configurar ambiente de teste
os.environ["TESTING"] = "true"

from bank_credit.app.database import Base, get_db
from bank_credit.app.main import app
from bank_credit.app.routers.auth import create_access_token
from bank_credit.app.models import Client
from bank_credit.app.routers.auth import get_password_hash

# Configuração do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    user = Client(username="test_user", email="test_user@example.com", hashed_password=get_password_hash("test_password"), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_token(test_user):
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def authorized_client(client, test_user_token):
    client.headers = {**client.headers, "Authorization": f"Bearer {test_user_token}"}
    return client
