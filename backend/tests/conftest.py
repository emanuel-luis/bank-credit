import itertools
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Test-only values, set before the app modules read the settings.
os.environ["SECRET_KEY"] = "test-secret-" + "x" * 52
os.environ["DATABASE_URL"] = "sqlite://"

from bank_credit.app.db import Base, get_db
from bank_credit.app.deps import get_now
from bank_credit.app.domain import workflow
from bank_credit.app.domain.documents import with_cnpj_check_digits, with_cpf_check_digits
from bank_credit.app.domain.enums import REQUIRED_DOCUMENTS, UserRole
from bank_credit.app.domain.reference import ensure_reference_data
from bank_credit.app.main import create_app
from bank_credit.app.models import Client, CreditRequest, Employee, Sector, User
from bank_credit.app.security import create_access_token, get_password_hash

T0 = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)
PASSWORD = "test_password"
_PASSWORD_HASH = get_password_hash(PASSWORD)  # Argon2 is slow: hash once
_seq = itertools.count(1)


@dataclass
class Clock:
    now: datetime


@pytest.fixture
def clock() -> Clock:
    return Clock(T0)


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection: Any, _record: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        ensure_reference_data(session)
        session.commit()
        yield session


@pytest.fixture
def test_app(db: Session, clock: Clock) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_now] = lambda: clock.now
    with TestClient(app) as test_client:
        yield test_client


def valid_cnpj() -> str:
    return with_cnpj_check_digits(f"{next(_seq):08d}0001")


def valid_cpf() -> str:
    return with_cpf_check_digits(f"{100_000_000 + next(_seq)}")


@pytest.fixture
def client_payload() -> Callable[[], dict[str, Any]]:
    """A valid body for POST /auth/register/client, new document and email on every call."""

    def make() -> dict[str, Any]:
        n = next(_seq)
        return {
            "cnpj": valid_cnpj(),
            "trade_name": f"Trade {n}",
            "legal_name": f"Legal {n} Ltda",
            "cnae_primary": "6201-5/01",
            "cnae_primary_desc": "Custom software development",
            "legal_nature_code": "2062",
            "legal_nature_desc": "Limited company",
            "street": "Rua Exemplo",
            "number": "100",
            "postal_code": "01310100",
            "district": "Centro",
            "city": "Sao Paulo",
            "state": "SP",
            "user": {
                "full_name": f"Customer {n}",
                "phone": "11987654321",
                "email": f"customer{n}@bank-demo.org",
                "password": "a-long-enough-password",
            },
        }

    return make


@pytest.fixture
def make_customer(db: Session) -> Callable[[], User]:
    def make() -> User:
        n = next(_seq)
        user = User(
            email=f"client{n}@bank-demo.org",
            full_name=f"Client {n}",
            phone="11987654321",
            hashed_password=_PASSWORD_HASH,
            role=UserRole.CUSTOMER,
            created_at=T0,
        )
        user.client = Client(
            cnpj=valid_cnpj(),
            trade_name=f"Trade {n}",
            legal_name=f"Legal {n} Ltda",
            cnae_primary="6201-5/01",
            cnae_primary_desc="Custom software development",
            legal_nature_code="2062",
            legal_nature_desc="Limited company",
            street="Rua Exemplo",
            number="100",
            postal_code="01310100",
            district="Centro",
            city="Sao Paulo",
            state="SP",
        )
        db.add(user)
        db.commit()
        return user

    return make


@pytest.fixture
def make_employee(db: Session) -> Callable[..., User]:
    def make(role: UserRole = UserRole.STAFF, sector: str | int | None = None) -> User:
        n = next(_seq)
        sector_id = (
            db.scalar(select(Sector.id).where(Sector.code == sector))
            if isinstance(sector, str)
            else sector
        )
        user = User(
            email=f"employee{n}@bank-demo.org",
            full_name=f"Employee {n}",
            phone="11987654321",
            hashed_password=_PASSWORD_HASH,
            role=role,
            created_at=T0,
        )
        user.employee = Employee(employee_number=f"E{n:05d}", cpf=valid_cpf(), sector_id=sector_id)
        db.add(user)
        db.commit()
        return user

    return make


@pytest.fixture
def customer(make_customer: Callable[[], User]) -> User:
    return make_customer()


@pytest.fixture
def other_customer(make_customer: Callable[[], User]) -> User:
    return make_customer()


@pytest.fixture
def retail_staff(make_employee: Callable[..., User]) -> User:
    return make_employee(UserRole.STAFF, "retail_center")


@pytest.fixture
def admin(make_employee: Callable[..., User]) -> User:
    return make_employee(UserRole.ADMIN, None)


@pytest.fixture
def submit(db: Session) -> Callable[..., CreditRequest]:
    def make(
        customer: User,
        amount: str = "100000.00",
        at: datetime = T0,
        purpose: str = "Working capital",
    ) -> CreditRequest:
        assert customer.client is not None
        request = workflow.submit_request(
            db,
            customer.client,
            customer,
            at,
            amount=Decimal(amount),
            purpose=purpose,
            term_days=90,
            deliver_date=(at + timedelta(days=30)).date(),
            documents=REQUIRED_DOCUMENTS,
        )
        db.commit()
        return request

    return make


@pytest.fixture
def auth() -> Callable[[User], dict[str, str]]:
    def headers(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user.email)}"}

    return headers
