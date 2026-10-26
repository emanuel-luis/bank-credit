"""Aggregates computed in plain Python from request_events, to check the SQL views against.

Deliberately written without looking at the view SQL: it walks each request's events in order,
skips SLA_BREACHED, and pairs every entry into IN_REVIEW with the next event.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import EventType, RequestStatus
from bank_credit.app.models import RequestEvent, Sector, Stage

AS_OF = datetime(2026, 3, 1, tzinfo=UTC)
FUTURE = datetime(2999, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Interval:
    request_id: int
    entry_seq: int
    stage: str
    sector: str
    entered_at: datetime
    exited_at: datetime | None
    exit_event: str | None
    sla_due_at: datetime | None

    @property
    def breached(self) -> bool:
        assert self.exited_at is not None and self.sla_due_at is not None
        return self.exited_at > self.sla_due_at

    @property
    def seconds(self) -> float:
        assert self.exited_at is not None
        return (self.exited_at - self.entered_at).total_seconds()


def monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def python_intervals(engine: Engine) -> list[Interval]:
    with Session(engine) as db:
        rows = db.execute(
            select(RequestEvent, Stage.code, Sector.code)
            .join(Stage, Stage.id == RequestEvent.stage_id)
            .join(Sector, Sector.id == RequestEvent.sector_id)
            .order_by(RequestEvent.request_id, RequestEvent.seq)
        ).all()
    by_request: dict[int, list[tuple[RequestEvent, str, str]]] = defaultdict(list)
    for event, stage, sector in rows:
        if event.event_type is not EventType.SLA_BREACHED:
            by_request[event.request_id].append((event, stage, sector))
    intervals = []
    for request_id, events in by_request.items():
        for i, (event, stage, sector) in enumerate(events):
            if event.to_status is not RequestStatus.IN_REVIEW:
                continue
            nxt = events[i + 1][0] if i + 1 < len(events) else None
            intervals.append(
                Interval(
                    request_id,
                    event.seq,
                    stage,
                    sector,
                    event.occurred_at,
                    nxt.occurred_at if nxt else None,
                    nxt.event_type.value if nxt else None,
                    event.sla_due_at,
                )
            )
    return intervals


def rate(breached: int, closed: int) -> Decimal:
    return (Decimal(breached) / Decimal(closed)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
