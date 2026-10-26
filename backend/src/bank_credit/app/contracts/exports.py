"""Data contracts of the exported datasets: one pydantic model per dataset row.

A contract is the promise made to whoever reads the files: column names, types and nullability.
Changing a column, its type or its meaning bumps `schema_version` (and the old files stay as
they were). Field order is the column order of the file.
"""

import types
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar, Union, get_args, get_origin

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from bank_credit.app.domain.enums import EventType, RequestStatus


class ExportRow(BaseModel):
    """Base of every dataset row. Unknown columns are an error, not silently dropped."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset: ClassVar[str]
    schema_version: ClassVar[int]
    # Where the rows come from: the table or view the export reads.
    source: ClassVar[str]


class RequestEventRow(ExportRow):
    """One row of the append-only request_events log. Grain: (request_id, seq)."""

    dataset: ClassVar[str] = "request_events"
    schema_version: ClassVar[int] = 1
    source: ClassVar[str] = "request_events"

    id: int
    request_id: int
    seq: int = Field(ge=1)
    event_type: EventType
    from_status: RequestStatus | None
    to_status: RequestStatus
    stage_code: str
    sector_code: str
    sla_due_at: AwareDatetime | None
    actor_user_id: int | None
    job_run_id: uuid.UUID | None
    reason: str | None
    occurred_at: AwareDatetime
    recorded_at: AwareDatetime


class StageIntervalRow(ExportRow):
    """One row of v_request_stage_intervals. Grain: (request_id, entry_seq)."""

    dataset: ClassVar[str] = "stage_intervals"
    schema_version: ClassVar[int] = 1
    source: ClassVar[str] = "v_request_stage_intervals"

    request_id: int
    entry_seq: int = Field(ge=1)
    stage_code: str
    stage_position: int
    sector_code: str
    entered_at: AwareDatetime
    exited_at: AwareDatetime | None
    exit_event: EventType | None
    sla_due_at: AwareDatetime | None
    duration_s: Decimal | None
    sla_breached: bool | None


class SlaBreachWeeklyRow(ExportRow):
    """One row of v_sla_breach_rate_weekly. Grain: (sector_code, week_start)."""

    dataset: ClassVar[str] = "sla_breach_weekly"
    schema_version: ClassVar[int] = 1
    source: ClassVar[str] = "v_sla_breach_rate_weekly"

    sector_code: str
    week_start: date
    closed: int = Field(ge=0)
    breached: int = Field(ge=0)
    breach_rate: Decimal


CONTRACTS: dict[str, type[ExportRow]] = {
    c.dataset: c for c in (RequestEventRow, StageIntervalRow, SlaBreachWeeklyRow)
}

_TYPE_NAMES: tuple[tuple[type, str], ...] = (
    (bool, "boolean"),  # before int: bool is an int subclass
    (int, "integer"),
    (Decimal, "decimal"),
    (datetime, "timestamp_utc"),  # before date: datetime is a date subclass
    (date, "date"),
    (uuid.UUID, "uuid"),
    (str, "string"),  # also the StrEnums
)


def columns_of(contract: type[ExportRow]) -> list[dict[str, str | bool]]:
    """The manifest's column list: name, logical type and nullability, in file order."""
    columns: list[dict[str, str | bool]] = []
    for name, field in contract.model_fields.items():
        annotation = field.annotation
        nullable = False
        if get_origin(annotation) in (Union, types.UnionType):
            args = [a for a in get_args(annotation) if a is not type(None)]
            nullable = len(args) < len(get_args(annotation))
            annotation = args[0]
        if annotation is AwareDatetime:
            annotation = datetime
        type_name = next(
            n for t, n in _TYPE_NAMES if isinstance(annotation, type) and issubclass(annotation, t)
        )
        columns.append({"name": name, "type": type_name, "nullable": nullable})
    return columns
