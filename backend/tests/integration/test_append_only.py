from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from bank_credit.app.domain import workflow
from bank_credit.app.models import RequestEvent, User

pytestmark = pytest.mark.integration

NOW = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)


@pytest.fixture
def engine_with_event(seeded_engine: Engine) -> Engine:
    with Session(seeded_engine) as db:
        customer = db.scalar(select(User).where(User.email == "customer1@example.com"))
        assert customer is not None and customer.client is not None
        workflow.submit_request(
            db,
            customer.client,
            customer,
            NOW,
            amount=Decimal("1000.00"),
            purpose="Working capital",
            term_days=30,
            deliver_date=NOW.date(),
        )
        db.commit()
    return seeded_engine


def _event_count(engine: Engine) -> int:
    with engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(RequestEvent)) or 0


def test_update_is_rejected(engine_with_event):
    with pytest.raises(DBAPIError, match="append-only"), engine_with_event.begin() as connection:
        connection.execute(text("UPDATE request_events SET reason = 'changed'"))
    with engine_with_event.connect() as connection:
        assert connection.scalar(select(func.count()).where(RequestEvent.reason.is_not(None))) == 0


def test_delete_is_rejected(engine_with_event):
    with pytest.raises(DBAPIError, match="append-only"), engine_with_event.begin() as connection:
        connection.execute(text("DELETE FROM request_events"))
    assert _event_count(engine_with_event) == 1


def test_truncate_is_allowed(engine_with_event):
    with engine_with_event.begin() as connection:
        connection.execute(text("TRUNCATE request_events"))
    assert _event_count(engine_with_event) == 0
