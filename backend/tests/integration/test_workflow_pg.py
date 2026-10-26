from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from bank_credit.app.domain import workflow
from bank_credit.app.domain.enums import REQUIRED_DOCUMENTS, Action, RequestStatus, UserRole
from bank_credit.app.jobs.simulate import simulate
from bank_credit.app.models import CreditRequest, Employee, RequestEvent, Sector, User

pytestmark = pytest.mark.integration

NOW = datetime(2026, 1, 5, 10, 0, 0, 123456, tzinfo=UTC)


def _submit(engine: Engine, amount: str, at: datetime = NOW) -> int:
    with Session(engine, expire_on_commit=False) as db:
        customer = db.scalar(select(User).where(User.email == "customer1@example.com"))
        assert customer is not None and customer.client is not None
        request = workflow.submit_request(
            db,
            customer.client,
            customer,
            at,
            amount=Decimal(amount),
            purpose="Working capital",
            term_days=30,
            deliver_date=at.date(),
            documents=REQUIRED_DOCUMENTS,
        )
        db.commit()
        return request.id


def test_numeric_and_timestamptz_round_trip_exactly(seeded_engine):
    at = datetime(2026, 1, 5, 7, 0, 0, 123456, tzinfo=timezone(timedelta(hours=-3)))
    request_id = _submit(seeded_engine, "4799999.99", at)

    with Session(seeded_engine) as db:
        request = db.get(CreditRequest, request_id)
        assert request is not None
        assert request.amount == Decimal("4799999.99")
        assert request.current_sector.code == "retail_center"  # just under the 4,800,000.00 band
        assert request.submitted_at == at
        assert request.submitted_at.utcoffset() == timedelta(0)
        assert request.submitted_at.microsecond == 123456
        assert request.expires_at == at + workflow.EXPIRY
        event = db.scalar(select(RequestEvent).where(RequestEvent.request_id == request_id))
        assert event is not None and event.occurred_at == at

    with seeded_engine.connect() as connection:
        types = connection.execute(
            text(
                "SELECT pg_typeof(amount)::text, pg_typeof(submitted_at)::text FROM credit_requests"
            )
        ).one()
    assert tuple(types) == ("numeric", "timestamp with time zone")


def test_band_boundary_routes_to_mid_large_center(seeded_engine):
    request_id = _submit(seeded_engine, "4800000.00")
    with Session(seeded_engine) as db:
        request = db.get(CreditRequest, request_id)
        assert request is not None
        assert request.amount == Decimal("4800000.00")
        assert request.current_sector.code == "mid_large_center"


def test_two_sessions_racing_the_same_transition_only_one_wins(seeded_engine):
    request_id = _submit(seeded_engine, "100000.00")
    with Session(seeded_engine) as db:
        staff_id = db.scalars(
            select(User.id)
            .join(Employee)
            .join(Sector, Sector.id == Employee.sector_id)
            .where(User.role == UserRole.STAFF, Sector.code == "retail_center")
        ).first()
    at = NOW + timedelta(hours=1)

    def attempt(_: int) -> str:
        with Session(seeded_engine) as db:
            request = db.get(CreditRequest, request_id)
            actor = db.get(User, staff_id)
            assert request is not None and actor is not None
            try:
                workflow.transition(db, request, Action.APPROVE, actor, at, expected_seq=1)
                db.commit()
            except workflow.StaleSequence:
                db.rollback()
                return "stale"
            return "approved"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(attempt, range(2)))
    assert outcomes == ["approved", "stale"]

    with Session(seeded_engine) as db:
        request = db.get(CreditRequest, request_id)
        assert request is not None
        assert request.last_seq == 2
        assert request.current_stage.code == "screening"
        events = select(func.count()).select_from(RequestEvent)
        assert db.scalar(events.where(RequestEvent.request_id == request_id)) == 2


def test_simulation_replays_to_the_projection_on_postgres(seeded_engine):
    as_of = datetime(2026, 3, 1, tzinfo=UTC)
    with Session(seeded_engine, expire_on_commit=False) as db:
        written = simulate(db, seed=3, as_of=as_of, days=45, clients=12)
        assert written > 0
        # Drop the identity map so the checks below read what Postgres stored.
        db.expire_all()
        requests = list(db.scalars(select(CreditRequest)))
        assert len(requests) >= 12
        for request in requests:
            events = list(
                db.scalars(select(RequestEvent).where(RequestEvent.request_id == request.id))
            )
            assert workflow.replay(events) == workflow.state_of(request)
        assert {r.status for r in requests} & {RequestStatus.APPROVED, RequestStatus.REJECTED}

        # --reset takes the Postgres TRUNCATE path and rebuilds the same history.
        all_events = select(func.count()).select_from(RequestEvent)
        events_before = db.scalar(all_events)
        assert simulate(db, seed=3, as_of=as_of, days=45, clients=12, reset=True) == written
        assert db.scalar(all_events) == events_before
