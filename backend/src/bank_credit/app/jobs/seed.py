"""Seed: reference data plus local demo users. Idempotent get-or-create by email."""

import logging
from datetime import UTC, datetime

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_credit.app.domain.documents import with_cnpj_check_digits, with_cpf_check_digits
from bank_credit.app.domain.enums import UserRole
from bank_credit.app.domain.reference import SECTORS, ensure_reference_data
from bank_credit.app.models import Client, Employee, Sector, User
from bank_credit.app.security import get_password_hash

logger = logging.getLogger("bank_credit.jobs.seed")

DEMO_CUSTOMERS = 3
ADMIN_EMAIL = "admin@example.com"

_CNAES = (
    ("4711-3/02", "Retail trade in supermarkets and hypermarkets"),
    ("4930-2/01", "Road freight transport"),
    ("6201-5/01", "Custom software development"),
    ("1091-1/02", "Bakery and confectionery manufacturing"),
    ("4120-4/00", "Building construction"),
)


def new_faker(seed: int) -> Faker:
    fake = Faker("pt_BR")
    fake.seed_instance(seed)
    return fake


def new_customer(fake: Faker, email: str, created_at: datetime) -> User:
    """A customer with a client, without a password yet. Synthetic data; the CNPJ digits are valid."""
    cnae, cnae_desc = fake.random_element(_CNAES)
    company = fake.company()
    user = User(
        email=email,
        full_name=fake.name(),
        phone=fake.numerify("119########"),
        hashed_password="",
        role=UserRole.CUSTOMER,
        created_at=created_at,
    )
    user.client = Client(
        cnpj=with_cnpj_check_digits(fake.numerify("########") + "0001"),
        trade_name=company,
        legal_name=f"{company} Ltda",
        cnae_primary=cnae,
        cnae_primary_desc=cnae_desc,
        legal_nature_code="2062",
        legal_nature_desc="Sociedade Empresária Limitada",
        street=fake.street_name(),
        number=fake.building_number(),
        postal_code=fake.numerify("########"),
        district=fake.bairro(),
        city=fake.city(),
        state=fake.estado_sigla(),
    )
    return user


def _new_employee(
    fake: Faker, email: str, role: UserRole, sector: Sector | None, number: int
) -> User:
    user = User(
        email=email,
        full_name=fake.name(),
        phone=fake.numerify("119########"),
        hashed_password="",
        role=role,
        created_at=datetime.now(UTC),
    )
    user.employee = Employee(
        employee_number=f"E{number:05d}",
        cpf=with_cpf_check_digits(fake.numerify("#########")),
        sector_id=sector.id if sector else None,
    )
    return user


def seed(db: Session, demo_password: str) -> int:
    """Create reference data and demo users that do not exist yet. Returns the users created.

    Does not commit. Fake values are drawn for every slot in a fixed order, so a user gets
    the same data whether or not its neighbours already existed.
    """
    ensure_reference_data(db)
    sectors = {s.code: s for s in db.scalars(select(Sector))}
    existing = set(db.scalars(select(User.email)))
    fake = new_faker(0)
    password: str | None = None  # hashing is slow: hash once, only when something is created
    created = 0

    slots: list[tuple[str, UserRole, Sector | None]] = [(ADMIN_EMAIL, UserRole.ADMIN, None)]
    for code in SECTORS:
        slots.append((f"manager.{code}@example.com", UserRole.MANAGER, sectors[code]))
        slots.extend(
            (f"staff{i}.{code}@example.com", UserRole.STAFF, sectors[code]) for i in (1, 2)
        )
    users = [
        _new_employee(fake, email, role, sector, number)
        for number, (email, role, sector) in enumerate(slots, start=1)
    ]
    users += [
        new_customer(fake, f"customer{i}@example.com", datetime.now(UTC))
        for i in range(1, DEMO_CUSTOMERS + 1)
    ]
    for user in users:
        if user.email in existing:
            continue
        password = password or get_password_hash(demo_password)
        user.hashed_password = password
        db.add(user)
        created += 1
    db.flush()
    logger.info("seed created %d users", created)
    return created
