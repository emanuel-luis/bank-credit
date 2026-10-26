"""The request workflow: the only writer of request state.

Every change is an append-only RequestEvent plus an update of the projection columns on
CreditRequest, in the caller's transaction. Functions here flush but never commit. Time is
always a tz-aware parameter.

Lazy expiry: transition() writes EXPIRED (and a due SLA_BREACHED before it) and then raises
RequestExpired. The caller must commit that write before reporting the error.
"""

import uuid
from dataclasses import dataclass, fields, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import (
    TERMINAL_STATUSES,
    Action,
    EventType,
    RequestStatus,
    UserRole,
)
from bank_credit.app.models import (
    Client,
    CreditRequest,
    RequestEvent,
    Stage,
    StageRoute,
    User,
)
from bank_credit.app.notifications import notify_request_event

EXPIRY = timedelta(days=45)


# --- Errors ---


class WorkflowError(Exception):
    """Base class. status_code and code feed the API error body {detail, code}."""

    status_code = 409
    code = "workflow_error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.__name__
        super().__init__(self.detail)


class Forbidden(WorkflowError):
    status_code = 403
    code = "forbidden"


class InvalidTransition(WorkflowError):
    code = "invalid_transition"


class StaleSequence(WorkflowError):
    code = "stale_seq"


class RequestExpired(WorkflowError):
    code = "request_expired"


class ClockWentBackwards(WorkflowError):
    code = "clock_went_backwards"


class ReasonRequired(WorkflowError):
    status_code = 422
    code = "reason_required"


class InvalidAmount(WorkflowError):
    status_code = 422
    code = "invalid_amount"


class InvalidDeliverDate(WorkflowError):
    status_code = 422
    code = "invalid_deliver_date"


# --- The transition table ---


class Party(StrEnum):
    OWNER = "owner"  # the customer who owns the request
    REVIEWER = "reviewer"  # staff or manager of the current sector, or an admin


@dataclass(frozen=True)
class Transition:
    event: EventType
    party: Party
    from_statuses: frozenset[RequestStatus]  # empty: the request does not exist yet
    to_status: RequestStatus | None  # None: depends on the stage (approve)
    needs_reason: bool = False


_IN_REVIEW = RequestStatus.IN_REVIEW
_RETURNED = RequestStatus.RETURNED

TRANSITIONS: dict[Action, Transition] = {
    Action.SUBMIT: Transition(EventType.SUBMITTED, Party.OWNER, frozenset(), _IN_REVIEW),
    Action.APPROVE: Transition(
        EventType.STAGE_APPROVED, Party.REVIEWER, frozenset({_IN_REVIEW}), None
    ),
    Action.RETURN: Transition(
        EventType.RETURNED, Party.REVIEWER, frozenset({_IN_REVIEW}), _RETURNED, needs_reason=True
    ),
    Action.RESUBMIT: Transition(
        EventType.RESUBMITTED, Party.OWNER, frozenset({_RETURNED}), _IN_REVIEW
    ),
    Action.REJECT: Transition(
        EventType.REJECTED,
        Party.REVIEWER,
        frozenset({_IN_REVIEW}),
        RequestStatus.REJECTED,
        needs_reason=True,
    ),
    Action.CANCEL: Transition(
        EventType.CANCELLED,
        Party.OWNER,
        frozenset({_IN_REVIEW, _RETURNED}),
        RequestStatus.CANCELLED,
    ),
}


# --- Projection: one pure function shared by the service and replay ---


@dataclass(frozen=True)
class RequestState:
    """The projection columns of CreditRequest that events determine."""

    status: RequestStatus
    current_stage_id: int
    current_sector_id: int
    sla_due_at: datetime | None
    sla_breached_at: datetime | None
    closed_at: datetime | None
    last_seq: int
    stage_entered_at: datetime
    updated_at: datetime
    submitted_at: datetime
    expires_at: datetime


def apply_event(state: RequestState | None, event: RequestEvent) -> RequestState:
    if event.event_type is EventType.SUBMITTED:
        return RequestState(
            status=event.to_status,
            current_stage_id=event.stage_id,
            current_sector_id=event.sector_id,
            sla_due_at=event.sla_due_at,
            sla_breached_at=None,
            closed_at=None,
            last_seq=event.seq,
            stage_entered_at=event.occurred_at,
            updated_at=event.occurred_at,
            submitted_at=event.occurred_at,
            expires_at=event.occurred_at + EXPIRY,
        )
    if state is None:
        raise ValueError("the first event of a request must be SUBMITTED")
    # Events that put the request (back) in a stage start a new SLA clock.
    entering = event.to_status is _IN_REVIEW and event.event_type is not EventType.SLA_BREACHED
    if event.event_type is EventType.SLA_BREACHED:
        breached_at = event.occurred_at
    else:
        breached_at = None if entering else state.sla_breached_at
    return replace(
        state,
        status=event.to_status,
        current_stage_id=event.stage_id,
        current_sector_id=event.sector_id,
        sla_due_at=event.sla_due_at,
        sla_breached_at=breached_at,
        closed_at=event.occurred_at if event.to_status in TERMINAL_STATUSES else None,
        last_seq=event.seq,
        stage_entered_at=event.occurred_at if entering else state.stage_entered_at,
        updated_at=event.occurred_at,
    )


def replay(events: list[RequestEvent]) -> RequestState:
    """Rebuild a request's state from its events alone."""
    state: RequestState | None = None
    for event in sorted(events, key=lambda e: e.seq):
        state = apply_event(state, event)
    if state is None:
        raise ValueError("no events")
    return state


def state_of(request: CreditRequest) -> RequestState:
    return RequestState(**{f.name: getattr(request, f.name) for f in fields(RequestState)})


# --- Helpers ---


def _require_aware(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware (UTC)")


def _is_owner(request: CreditRequest, user: User) -> bool:
    return (
        user.role is UserRole.CUSTOMER
        and user.client is not None
        and user.client.id == request.client_id
    )


def _is_reviewer(request: CreditRequest, user: User) -> bool:
    if user.role is UserRole.ADMIN:
        return True
    return (
        user.role in (UserRole.STAFF, UserRole.MANAGER)
        and user.employee is not None
        and user.employee.sector_id == request.current_sector_id
    )


def _is_party(request: CreditRequest, user: User, party: Party) -> bool:
    return _is_owner(request, user) if party is Party.OWNER else _is_reviewer(request, user)


def resolve_route(db: Session, stage: Stage, amount: Decimal) -> StageRoute:
    """The route whose half-open band [min_amount, max_amount) holds the amount."""
    for route in db.scalars(select(StageRoute).where(StageRoute.stage_id == stage.id)):
        if route.min_amount <= amount and (route.max_amount is None or amount < route.max_amount):
            return route
    raise LookupError(f"no route for stage {stage.code} and amount {amount}")


def _stages_after(db: Session, position: int | None) -> list[Stage]:
    query = select(Stage).order_by(Stage.position)
    if position is not None:
        query = query.where(Stage.position > position)
    return list(db.scalars(query))


def estimated_completion_at(db: Session, request: CreditRequest) -> datetime | None:
    """Current SLA deadline plus the SLA hours of the remaining stages for the request's band."""
    if request.sla_due_at is None:
        return None
    remaining = _stages_after(db, request.current_stage.position)
    hours = sum(resolve_route(db, stage, request.amount).sla_hours for stage in remaining)
    return request.sla_due_at + timedelta(hours=hours)


def allowed_actions(request: CreditRequest, user: User, now: datetime) -> list[Action]:
    """Actions this user can take now. Empty once the request is closed or past its expiry."""
    _require_aware(now)
    if request.status in TERMINAL_STATUSES or now >= request.expires_at:
        return []
    return [
        action
        for action, rule in TRANSITIONS.items()
        if request.status in rule.from_statuses and _is_party(request, user, rule.party)
    ]


def _emit(
    db: Session,
    request: CreditRequest,
    event_type: EventType,
    to_status: RequestStatus,
    occurred_at: datetime,
    *,
    stage: Stage,
    sector_id: int,
    sla_due_at: datetime | None,
    actor: User | None = None,
    reason: str | None = None,
    job_run_id: uuid.UUID | None = None,
) -> RequestEvent:
    if occurred_at < request.updated_at:
        raise ClockWentBackwards(
            f"event at {occurred_at.isoformat()} is before the request's last event "
            f"at {request.updated_at.isoformat()}"
        )
    first = request.last_seq == 0
    event = RequestEvent(
        request_id=request.id,
        seq=request.last_seq + 1,
        event_type=event_type,
        from_status=None if first else request.status,
        to_status=to_status,
        stage_id=stage.id,
        sector_id=sector_id,
        sla_due_at=sla_due_at,
        actor_user_id=actor.id if actor else None,
        job_run_id=job_run_id,
        reason=reason,
        occurred_at=occurred_at,
    )
    new_state = apply_event(None if first else state_of(request), event)
    for f in fields(new_state):
        setattr(request, f.name, getattr(new_state, f.name))
    db.add(event)
    db.flush()
    db.expire(request, ["current_stage", "current_sector"])  # the FK columns changed
    notify_request_event(db, request, event)
    return event


# --- Public operations ---


def submit_request(
    db: Session,
    client: Client,
    actor: User,
    now: datetime,
    *,
    amount: Decimal,
    purpose: str,
    term_days: int,
    deliver_date: date,
) -> CreditRequest:
    _require_aware(now)
    if actor.role is not UserRole.CUSTOMER or client.user_id != actor.id:
        raise Forbidden("only the customer who owns the client can submit a request")
    if amount <= 0:
        raise InvalidAmount("amount must be greater than 0")
    if deliver_date < now.date():
        raise InvalidDeliverDate("deliver_date must not be in the past")
    first_stage = _stages_after(db, None)[0]
    route = resolve_route(db, first_stage, amount)
    request = CreditRequest(
        client_id=client.id,
        amount=amount,
        purpose=purpose,
        term_days=term_days,
        deliver_date=deliver_date,
        status=_IN_REVIEW,
        current_stage_id=first_stage.id,
        current_sector_id=route.sector_id,
        submitted_at=now,
        expires_at=now + EXPIRY,
        stage_entered_at=now,
        sla_due_at=now + timedelta(hours=route.sla_hours),
        last_seq=0,
        updated_at=now,
    )
    db.add(request)
    db.flush()
    _emit(
        db,
        request,
        TRANSITIONS[Action.SUBMIT].event,
        _IN_REVIEW,
        now,
        stage=first_stage,
        sector_id=route.sector_id,
        sla_due_at=now + timedelta(hours=route.sla_hours),
        actor=actor,
    )
    return request


def apply_due_system_events(
    db: Session, request: CreditRequest, now: datetime, job_run_id: uuid.UUID | None = None
) -> list[RequestEvent]:
    """Emit SLA_BREACHED, then EXPIRED, stamped with their deadlines. Idempotent."""
    _require_aware(now)
    if request.status in TERMINAL_STATUSES:
        return []
    events: list[RequestEvent] = []
    stage, sector_id = request.current_stage, request.current_sector_id
    due = request.sla_due_at
    # A breach only counts while the request is alive: one due after expiry never happens.
    if (
        request.status is _IN_REVIEW
        and due is not None
        and request.sla_breached_at is None
        and due <= request.expires_at
        and now >= due
    ):
        events.append(
            _emit(
                db,
                request,
                EventType.SLA_BREACHED,
                _IN_REVIEW,
                due,
                stage=stage,
                sector_id=sector_id,
                sla_due_at=due,
                job_run_id=job_run_id,
            )
        )
    if now >= request.expires_at:
        events.append(
            _emit(
                db,
                request,
                EventType.EXPIRED,
                RequestStatus.EXPIRED,
                request.expires_at,
                stage=stage,
                sector_id=sector_id,
                sla_due_at=None,
                job_run_id=job_run_id,
            )
        )
    return events


def transition(
    db: Session,
    request: CreditRequest,
    action: Action,
    actor: User,
    now: datetime,
    reason: str | None = None,
    job_run_id: uuid.UUID | None = None,
    expected_seq: int | None = None,
) -> RequestEvent:
    _require_aware(now)
    rule = TRANSITIONS[action]
    if action is Action.SUBMIT:
        raise InvalidTransition("use submit_request to create a request")
    db.refresh(request, with_for_update=True)

    if not _is_party(request, actor, rule.party):
        raise Forbidden(f"this user cannot {action.value} this request")
    if expected_seq is not None and expected_seq != request.last_seq:
        raise StaleSequence(f"expected seq {expected_seq}, request is at {request.last_seq}")
    if request.status is RequestStatus.EXPIRED:
        raise RequestExpired("the request expired")
    if request.status not in rule.from_statuses:
        raise InvalidTransition(f"cannot {action.value} a request in status {request.status}")
    if rule.needs_reason and not (reason and reason.strip()):
        raise ReasonRequired(f"a reason is required to {action.value}")
    # Validation is done before this point so a rejected call writes nothing.
    if any(e.event_type is EventType.EXPIRED for e in apply_due_system_events(db, request, now)):
        raise RequestExpired("the request expired")

    stage = request.current_stage
    sector_id = request.current_sector_id
    sla_due_at: datetime | None = None
    to_status = rule.to_status
    if action is Action.APPROVE:
        later = _stages_after(db, stage.position)
        if later:
            stage = later[0]
            route = resolve_route(db, stage, request.amount)
            sector_id = route.sector_id
            sla_due_at = now + timedelta(hours=route.sla_hours)
            to_status = _IN_REVIEW
        else:
            to_status = RequestStatus.APPROVED
    elif action is Action.RESUBMIT:
        route = resolve_route(db, stage, request.amount)
        sector_id = route.sector_id
        sla_due_at = now + timedelta(hours=route.sla_hours)
    assert to_status is not None
    return _emit(
        db,
        request,
        rule.event,
        to_status,
        now,
        stage=stage,
        sector_id=sector_id,
        sla_due_at=sla_due_at,
        actor=actor,
        reason=reason.strip() if reason else None,
        job_run_id=job_run_id,
    )
