"""SLA analytics over the v_* SQL views (Postgres only). Managers see their sector, admins all.

Response shape: {data, generated_at, source_view}. Counts are integers; rates and hours are
Decimals, so they serialize as JSON strings like money does (decision 51).
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from bank_credit.app.db import get_db
from bank_credit.app.deps import get_now
from bank_credit.app.domain.enums import UserRole
from bank_credit.app.errors import ApiError
from bank_credit.app.models import User
from bank_credit.app.routers.auth import get_current_active_user

router = APIRouter()

DEFAULT_WEEKS = 12
DEFAULT_THROUGHPUT_DAYS = 90


class SlaBreachRateRow(BaseModel):
    sector_code: str
    week_start: date
    closed: int
    breached: int
    breach_rate: Decimal


class TimeInStageRow(BaseModel):
    stage_code: str
    sector_code: str
    week_start: date
    n: int
    avg_h: Decimal
    p50_h: Decimal
    p90_h: Decimal


class ThroughputRow(BaseModel):
    sector_code: str
    day: date
    entered: int
    approved: int
    returned: int
    rejected: int
    cancelled: int
    expired: int


class SlaBreachRateResponse(BaseModel):
    data: list[SlaBreachRateRow]
    generated_at: datetime
    source_view: str


class TimeInStageResponse(BaseModel):
    data: list[TimeInStageRow]
    generated_at: datetime
    source_view: str


class ThroughputResponse(BaseModel):
    data: list[ThroughputRow]
    generated_at: datetime
    source_view: str


@dataclass(frozen=True)
class Dataset:
    view: str
    date_column: str
    order_by: str
    weekly: bool  # date_column is a Monday: `from` is aligned to the start of its week
    default_days: int


SLA_BREACH_RATE = Dataset(
    "v_sla_breach_rate_weekly", "week_start", "week_start, sector_code", True, DEFAULT_WEEKS * 7
)
TIME_IN_STAGE = Dataset(
    "v_time_in_stage_weekly",
    "week_start",
    "week_start, sector_code, stage_code",
    True,
    DEFAULT_WEEKS * 7,
)
THROUGHPUT = Dataset(
    "v_throughput_daily", "day", "day, sector_code", False, DEFAULT_THROUGHPUT_DAYS
)

# (dataset, from, to, sector) -> rows. The query layer: tests inject a fake, since the views
# exist only on Postgres.
Reader = Callable[[Dataset, date, date, str | None], list[Mapping[str, Any]]]


def get_reader(db: Session = Depends(get_db)) -> Reader:
    def read(
        dataset: Dataset, start: date, end: date, sector: str | None
    ) -> list[Mapping[str, Any]]:
        # View and column names come from the constants above, never from the request.
        sql = (
            f"SELECT * FROM {dataset.view} "
            f"WHERE {dataset.date_column} BETWEEN :start AND :end"
            + (" AND sector_code = :sector" if sector else "")
            + f" ORDER BY {dataset.order_by}"
        )
        params: dict[str, Any] = {"start": start, "end": end}
        if sector:
            params["sector"] = sector
        return [dict(row) for row in db.execute(text(sql), params).mappings()]

    return read


def _scoped_sector(user: User, requested: str | None) -> str | None:
    """Admins may pick any sector; managers are held to their own."""
    if user.role is UserRole.ADMIN:
        return requested
    if user.role is not UserRole.MANAGER:
        raise ApiError(
            status.HTTP_403_FORBIDDEN, "Analytics are for managers and admins", "forbidden"
        )
    own = user.employee.sector.code if user.employee and user.employee.sector else None
    if own is None:
        raise ApiError(status.HTTP_403_FORBIDDEN, "Manager has no sector", "forbidden")
    if requested is not None and requested != own:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            f"Sector {requested} is not allowed for your role",
            "scope_not_allowed",
        )
    return own


def _fetch(
    dataset: Dataset,
    reader: Reader,
    user: User,
    now: datetime,
    from_: date | None,
    to: date | None,
    sector: str | None,
) -> list[Mapping[str, Any]]:
    sector = _scoped_sector(user, sector)
    end = to or now.date()
    start = from_ or end - timedelta(days=dataset.default_days)
    if start > end:
        raise ApiError(422, "from is after to", "invalid_range")
    if dataset.weekly:
        start -= timedelta(days=start.weekday())
    return reader(dataset, start, end, sector)


FromDate = Annotated[date | None, Query(alias="from", description="Default: to minus the window")]
ToDate = Annotated[date | None, Query(description="Default: today (UTC)")]
SectorCode = Annotated[str | None, Query(description="Sector code; managers get their own")]


@router.get("/sla-breach-rate", response_model=SlaBreachRateResponse)
def sla_breach_rate(
    from_: FromDate = None,
    to: ToDate = None,
    sector: SectorCode = None,
    reader: Reader = Depends(get_reader),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> SlaBreachRateResponse:
    """Weekly share of stage intervals that missed their SLA (default: last 12 weeks)."""
    rows = _fetch(SLA_BREACH_RATE, reader, user, now, from_, to, sector)
    return SlaBreachRateResponse(
        data=[SlaBreachRateRow.model_validate(r) for r in rows],
        generated_at=now,
        source_view=SLA_BREACH_RATE.view,
    )


@router.get("/time-in-stage", response_model=TimeInStageResponse)
def time_in_stage(
    from_: FromDate = None,
    to: ToDate = None,
    sector: SectorCode = None,
    reader: Reader = Depends(get_reader),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> TimeInStageResponse:
    """Weekly average, median and 90th percentile hours per stage (default: last 12 weeks)."""
    rows = _fetch(TIME_IN_STAGE, reader, user, now, from_, to, sector)
    return TimeInStageResponse(
        data=[TimeInStageRow.model_validate(r) for r in rows],
        generated_at=now,
        source_view=TIME_IN_STAGE.view,
    )


@router.get("/throughput", response_model=ThroughputResponse)
def throughput(
    from_: FromDate = None,
    to: ToDate = None,
    sector: SectorCode = None,
    reader: Reader = Depends(get_reader),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> ThroughputResponse:
    """Daily entries and exits per sector (default: last 90 days)."""
    rows = _fetch(THROUGHPUT, reader, user, now, from_, to, sector)
    return ThroughputResponse(
        data=[ThroughputRow.model_validate(r) for r in rows],
        generated_at=now,
        source_view=THROUGHPUT.view,
    )
