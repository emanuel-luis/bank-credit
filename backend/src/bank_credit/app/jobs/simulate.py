"""Synthetic request history, generated through the workflow service.

Deterministic for a given seed and as-of: one random.Random and one Faker instance, both seeded,
and every query that feeds a choice is ordered.
"""

import logging
import math
import random
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from bank_credit.app.domain import workflow
from bank_credit.app.domain.enums import (
    REQUIRED_DOCUMENTS,
    TERMINAL_STATUSES,
    Action,
    EventType,
    JobStatus,
    RequestStatus,
    UserRole,
)
from bank_credit.app.domain.reference import BAND_LIMIT, ensure_reference_data
from bank_credit.app.jobs.runs import job_run
from bank_credit.app.jobs.seed import new_customer, new_faker
from bank_credit.app.models import (
    Client,
    CreditRequest,
    Employee,
    JobRun,
    Notification,
    RequestEvent,
    Sector,
    User,
)
from bank_credit.app.security import get_password_hash

logger = logging.getLogger("bank_credit.jobs.simulate")

JOB_NAME = "simulate"
RETAIL_SHARE_Z = 1.036  # standard normal quantile of 0.85
SIGMA = 1.5  # log-normal spread of the amounts
# Per-stage outcome cumulative thresholds: approve 85%, return 8%, reject 5%, cancel 2%.
APPROVE_UNTIL, RETURN_UNTIL, REJECT_UNTIL = 0.85, 0.93, 0.98
RESUBMIT_PROBABILITY = 0.85
RESUBMIT_MEDIAN_HOURS = 36.0

PURPOSES = (
    "Working capital",
    "Equipment purchase",
    "Fleet renewal",
    "Inventory financing",
    "Facility expansion",
    "Receivables advance",
)
RETURN_REASONS = ("Missing documents", "Inconsistent financial statements", "Update the contract")
REJECT_REASONS = ("Credit policy", "Insufficient revenue", "Excessive leverage")


def default_as_of() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _count_rows(db: Session) -> int:
    return sum(
        db.scalar(select(func.count()).select_from(model)) or 0
        for model in (CreditRequest, RequestEvent, Notification, Client)
    )


def reset_data(db: Session) -> None:
    """Remove requests, events, notifications and the synthetic clients. Keeps users and runs."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text(
                "TRUNCATE request_events, request_documents, notifications, credit_requests "
                "RESTART IDENTITY CASCADE"
            )
        )
    else:
        # Raw SQL: request_events is append-only for the ORM, and a reset is the one exception.
        for table in ("request_events", "request_documents", "notifications", "credit_requests"):
            db.execute(text(f"DELETE FROM {table}"))
    synthetic = select(User.id).where(User.email.like("sim-%@example.com"))
    db.execute(delete(Client).where(Client.user_id.in_(synthetic)))
    db.execute(delete(User).where(User.id.in_(synthetic)))
    db.expire_all()


def _amount(rng: random.Random) -> Decimal:
    mu = math.log(float(BAND_LIMIT)) - RETAIL_SHARE_Z * SIGMA
    value = min(max(rng.lognormvariate(mu, SIGMA), 5_000.0), 500_000_000.0)
    return Decimal(f"{value:.2f}")


def _hours(value: float) -> timedelta:
    return timedelta(seconds=round(value * 3600))


def _staff_by_sector(db: Session) -> dict[int, list[User]]:
    staff: dict[int, list[User]] = {}
    rows = db.scalars(
        select(User)
        .join(Employee)
        .where(User.role == UserRole.STAFF, Employee.sector_id.is_not(None))
        .order_by(User.id)
    )
    for user in rows:
        assert user.employee is not None and user.employee.sector_id is not None
        staff.setdefault(user.employee.sector_id, []).append(user)
    missing = [s.code for s in db.scalars(select(Sector)) if s.id not in staff]
    if missing:
        raise RuntimeError(f"no staff in sectors {missing}: run `bank-credit seed` first")
    return staff


def _clients(db: Session, fake: Faker, seed: int, count: int, created_at: datetime) -> list[User]:
    """Get-or-create the synthetic customers for this seed."""
    token_hash = get_password_hash(secrets.token_urlsafe(32))  # nobody knows the token
    existing = {
        u.email: u for u in db.scalars(select(User).where(User.email.like(f"sim-{seed}-%")))
    }
    users = []
    for i in range(count):
        email = f"sim-{seed}-{i}@example.com"
        candidate = new_customer(fake, email, created_at)  # always drawn, so data stays stable
        if email in existing:
            users.append(existing[email])
            continue
        candidate.hashed_password = token_hash
        db.add(candidate)
        users.append(candidate)
    db.flush()
    return users


def _drive(
    db: Session,
    request: CreditRequest,
    owner: User,
    staff: dict[int, list[User]],
    rng: random.Random,
    as_of: datetime,
    run: JobRun,
) -> None:
    """Walk one request through the workflow until it closes or reaches as_of."""
    while request.status not in TERMINAL_STATUSES:
        reason: str | None = None
        if request.status is RequestStatus.RETURNED:
            if rng.random() >= RESUBMIT_PROBABILITY:
                break
            hours = rng.lognormvariate(math.log(RESUBMIT_MEDIAN_HOURS), 0.8)
            at = request.updated_at + _hours(hours)
            action, actor = Action.RESUBMIT, owner
        else:
            route = workflow.resolve_route(db, request.current_stage, request.amount)
            at = request.stage_entered_at + _hours(rng.uniform(0.3, 2.0) * route.sla_hours)
            roll = rng.random()
            actor = rng.choice(staff[request.current_sector_id])
            if roll < APPROVE_UNTIL:
                action = Action.APPROVE
            elif roll < RETURN_UNTIL:
                action, reason = Action.RETURN, rng.choice(RETURN_REASONS)
            elif roll < REJECT_UNTIL:
                action, reason = Action.REJECT, rng.choice(REJECT_REASONS)
            else:
                action, actor = Action.CANCEL, owner
        if at > as_of:
            break
        due = workflow.apply_due_system_events(db, request, at, run.run_id)
        if any(e.event_type is EventType.EXPIRED for e in due):
            break
        workflow.transition(db, request, action, actor, at, reason, run.run_id)
    workflow.apply_due_system_events(db, request, as_of, run.run_id)


def simulate(
    db: Session,
    seed: int = 42,
    as_of: datetime | None = None,
    days: int = 120,
    clients: int = 200,
    reset: bool = False,
) -> int:
    """Generate history and return the rows written. Run `seed` first: it creates the staff."""
    as_of = as_of or default_as_of()
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    as_of = as_of.astimezone(UTC)
    params = {"seed": seed, "as_of": as_of.isoformat(), "days": days, "clients": clients}
    if not reset:
        done = db.scalars(
            select(JobRun).where(JobRun.job_name == JOB_NAME, JobRun.status == JobStatus.SUCCEEDED)
        )
        if any(run.params == params for run in done):
            logger.info("simulate skipped: a succeeded run with %s exists", params)
            return 0

    with job_run(db, JOB_NAME, params) as run:
        if reset:
            reset_data(db)
        ensure_reference_data(db)
        staff = _staff_by_sector(db)
        rng = random.Random(seed)
        fake = new_faker(seed)
        before = _count_rows(db)
        start = as_of - timedelta(days=days)
        requests = 0
        for customer in _clients(db, fake, seed, clients, start):
            assert customer.client is not None
            for _ in range(rng.randint(1, 3)):
                at = start + timedelta(seconds=rng.randrange(days * 86400))
                request = workflow.submit_request(
                    db,
                    customer.client,
                    customer,
                    at,
                    amount=_amount(rng),
                    purpose=rng.choice(PURPOSES),
                    term_days=rng.choice((30, 60, 90, 180, 360)),
                    deliver_date=(at + timedelta(days=rng.randint(15, 90))).date(),
                    documents=REQUIRED_DOCUMENTS,
                )
                _drive(db, request, customer, staff, rng, as_of, run)
                requests += 1
        run.rows_read = 0
        run.rows_written = _count_rows(db) - before
        logger.info("simulate wrote %d requests and %d rows", requests, run.rows_written)
        written = run.rows_written
    return written
