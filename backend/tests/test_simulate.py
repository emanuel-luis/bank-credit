import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from bank_credit.app.db import Base
from bank_credit.app.domain.enums import REQUIRED_DOCUMENTS, EventType, JobStatus, RequestStatus
from bank_credit.app.domain.workflow import replay, state_of
from bank_credit.app.jobs import seed as seed_module
from bank_credit.app.jobs import simulate as simulate_module
from bank_credit.app.jobs.seed import seed
from bank_credit.app.jobs.simulate import simulate
from bank_credit.app.jobs.sla_check import sla_check
from bank_credit.app.models import (
    Client,
    CreditRequest,
    JobRun,
    Notification,
    RequestEvent,
    Sector,
    Stage,
    User,
)
from bank_credit.app.security import verify_password

AS_OF = datetime(2026, 3, 1, tzinfo=UTC)
SMALL = {"seed": 1, "as_of": AS_OF, "days": 60, "clients": 20}


def fresh_engine() -> Engine:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine


def simulated_db(real_hashes: bool = False, **overrides) -> Session:
    """A seeded and simulated database. Argon2 is slow, so hashes are fake unless asked for."""
    db = Session(fresh_engine(), expire_on_commit=False)
    with pytest.MonkeyPatch.context() as patch:
        if not real_hashes:
            for module in (seed_module, simulate_module):
                patch.setattr(module, "get_password_hash", lambda password: f"fake${password}")
        seed(db, "pw")
        db.commit()
        simulate(db, **{**SMALL, **overrides})
    return db


def event_digest(db: Session) -> str:
    rows = db.execute(
        select(
            RequestEvent.request_id,
            RequestEvent.seq,
            RequestEvent.event_type,
            RequestEvent.occurred_at,
            Stage.code,
            Sector.code,
        )
        .join(Stage, Stage.id == RequestEvent.stage_id)
        .join(Sector, Sector.id == RequestEvent.sector_id)
        .order_by(RequestEvent.request_id, RequestEvent.seq)
    )
    digest = hashlib.sha256()
    for request_id, seq, event_type, occurred_at, stage, sector in rows:
        line = (request_id, seq, str(event_type), occurred_at.isoformat(), stage, sector)
        digest.update(repr(line).encode())
    return digest.hexdigest()


def projection_matches_replay(db: Session) -> int:
    # Drop the identity map so the checks read stored rows, not in-memory objects.
    db.expire_all()
    requests = list(db.scalars(select(CreditRequest)))
    for request in requests:
        events = list(db.scalars(select(RequestEvent).where(RequestEvent.request_id == request.id)))
        assert replay(events) == state_of(request)
    return len(requests)


@pytest.fixture(scope="module")
def sim():
    db = simulated_db(real_hashes=True)
    yield db
    db.close()


def test_simulate_is_deterministic_for_a_seed_and_as_of(sim):
    assert event_digest(simulated_db()) == event_digest(sim)
    assert event_digest(simulated_db(seed=2)) != event_digest(sim)


def test_replay_matches_the_projection_for_every_request(sim):
    assert projection_matches_replay(sim) >= 20


def test_simulated_requests_declare_the_required_documents(sim):
    requests = sim.scalars(select(CreditRequest)).all()
    assert requests
    assert all({d.document_type for d in r.documents} == REQUIRED_DOCUMENTS for r in requests)


def test_history_has_every_kind_of_outcome(sim):
    types = set(sim.scalars(select(RequestEvent.event_type)))
    assert {EventType.SLA_BREACHED, EventType.RETURNED, EventType.RESUBMITTED} <= types
    statuses = set(sim.scalars(select(CreditRequest.status)))
    assert {RequestStatus.IN_REVIEW, RequestStatus.REJECTED, RequestStatus.APPROVED} <= statuses
    assert max(sim.scalars(select(RequestEvent.occurred_at))) <= AS_OF
    assert min(sim.scalars(select(CreditRequest.submitted_at))) >= AS_OF - timedelta(days=60)


def test_simulate_records_its_run(sim):
    run = sim.scalar(select(JobRun).where(JobRun.job_name == "simulate"))
    assert run.status is JobStatus.SUCCEEDED
    assert run.rows_written > 0
    assert run.params == {"seed": 1, "as_of": AS_OF.isoformat(), "days": 60, "clients": 20}
    tagged = (
        select(func.count()).select_from(RequestEvent).where(RequestEvent.job_run_id == run.run_id)
    )
    assert sim.scalar(tagged) > 0


def test_simulated_clients_cannot_log_in(sim):
    user = sim.scalar(select(User).where(User.email == "sim-1-0@example.com"))
    assert user.hashed_password.startswith("$argon2")
    assert not verify_password("demo1234", user.hashed_password)


def test_simulate_rerun_with_the_same_params_writes_nothing():
    db = simulated_db()
    models = (CreditRequest, RequestEvent, Notification, Client, JobRun)

    def count():
        return [db.scalar(select(func.count()).select_from(m)) for m in models]

    before = count()
    assert simulate(db, **SMALL) == 0
    assert count() == before


def test_simulate_reset_rebuilds_the_same_history():
    db = simulated_db()
    digest = event_digest(db)
    assert simulate(db, **SMALL, reset=True) > 0
    assert event_digest(db) == digest
    assert db.scalar(select(func.count()).select_from(Client)) == 23  # 3 demo + 20 synthetic


def test_simulate_without_seed_data_fails_clearly():
    db = Session(fresh_engine(), expire_on_commit=False)
    with pytest.raises(RuntimeError, match="bank-credit seed"):
        simulate(db, **SMALL)
    assert db.scalar(select(JobRun)).status is JobStatus.FAILED


def test_sla_check_catches_up_then_writes_nothing():
    db = simulated_db()
    assert sla_check(db, AS_OF) == 0  # simulate already applied everything due at as_of
    later = AS_OF + timedelta(days=60)
    assert sla_check(db, later) > 0
    late_types = select(RequestEvent.event_type).where(RequestEvent.occurred_at > AS_OF)
    types = set(db.scalars(late_types))
    assert EventType.EXPIRED in types
    assert types <= {EventType.SLA_BREACHED, EventType.EXPIRED}
    assert sla_check(db, later) == 0
    projection_matches_replay(db)
    runs = db.scalars(
        select(JobRun).where(JobRun.job_name == "sla-check").order_by(JobRun.started_at)
    )
    written = [r.rows_written for r in runs]
    assert written[0] == 0 and written[1] > 0 and written[2] == 0
