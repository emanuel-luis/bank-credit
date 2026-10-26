from datetime import timedelta
from decimal import Decimal

import pytest
from conftest import T0
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bank_credit.app.domain import workflow
from bank_credit.app.domain.enums import (
    REQUIRED_DOCUMENTS,
    Action,
    DocumentType,
    EventType,
    JobStatus,
    RequestStatus,
    UserRole,
)
from bank_credit.app.domain.reference import (
    BAND_LIMIT,
    ROUTES,
    STAGES,
    RouteSpec,
    ensure_reference_data,
    validate_routes,
)
from bank_credit.app.models import (
    AppendOnlyViolation,
    CreditRequest,
    JobRun,
    Notification,
    RequestEvent,
    Sector,
    Stage,
    StageRoute,
    User,
)

HOUR = timedelta(hours=1)


def events_of(db: Session, request: CreditRequest) -> list[RequestEvent]:
    return list(
        db.scalars(
            select(RequestEvent)
            .where(RequestEvent.request_id == request.id)
            .order_by(RequestEvent.seq)
        )
    )


def notifications_of(db: Session, request: CreditRequest) -> list[Notification]:
    return list(db.scalars(select(Notification).where(Notification.request_id == request.id)))


# --- Reference data ---


def test_reference_data_is_idempotent(db):
    counts = lambda: [
        db.scalar(select(func.count()).select_from(model)) for model in (Stage, Sector, StageRoute)
    ]
    assert counts() == [5, 3, 9]
    ensure_reference_data(db)
    ensure_reference_data(db)
    assert counts() == [5, 3, 9]
    assert [s.code for s in db.scalars(select(Stage).order_by(Stage.position))] == [
        code for code, _ in STAGES
    ]


def test_routes_constants_are_valid():
    validate_routes()


def test_validate_routes_rejects_gaps_overlaps_and_open_ends():
    first = ROUTES[0]
    others = [r for r in ROUTES if r is not first]
    gap = RouteSpec(first.stage, first.sector, Decimal(0), Decimal("1000.00"), 24)
    with pytest.raises(ValueError, match="gap or overlap"):
        validate_routes([gap, *others])
    overlap = RouteSpec(first.stage, first.sector, Decimal(0), BAND_LIMIT + 1, 24)
    with pytest.raises(ValueError, match="gap or overlap"):
        validate_routes([overlap, *others])
    with pytest.raises(ValueError, match="no routes"):
        validate_routes([r for r in ROUTES if r.stage != "screening"])
    capped = RouteSpec("disbursement", "disbursement_center", Decimal(0), Decimal("10.00"), 24)
    with pytest.raises(ValueError, match="unbounded"):
        validate_routes([r for r in ROUTES if r.stage != "disbursement"] + [capped])


# --- The transition table, checked against the specification ---

# action -> (who may do it, statuses it applies to, event written)
SPEC = {
    Action.APPROVE: (
        {"sector_staff", "sector_manager", "admin"},
        {RequestStatus.IN_REVIEW},
        EventType.STAGE_APPROVED,
    ),
    Action.RETURN: (
        {"sector_staff", "sector_manager", "admin"},
        {RequestStatus.IN_REVIEW},
        EventType.RETURNED,
    ),
    Action.REJECT: (
        {"sector_staff", "sector_manager", "admin"},
        {RequestStatus.IN_REVIEW},
        EventType.REJECTED,
    ),
    Action.RESUBMIT: ({"owner"}, {RequestStatus.RETURNED}, EventType.RESUBMITTED),
    Action.CANCEL: (
        {"owner"},
        {RequestStatus.IN_REVIEW, RequestStatus.RETURNED},
        EventType.CANCELLED,
    ),
}
ACTORS = [
    "owner",
    "other_customer",
    "sector_staff",
    "sector_manager",
    "other_sector_staff",
    "admin",
]


def test_transition_table_matches_the_specification():
    assert {a for a in workflow.TRANSITIONS if a is not Action.SUBMIT} == set(SPEC)
    for action, (_, statuses, event) in SPEC.items():
        rule = workflow.TRANSITIONS[action]
        assert rule.from_statuses == statuses
        assert rule.event is event


@pytest.fixture
def build_in_status(db, customer, admin, submit, make_employee):
    """A request in the given status, plus a staff member of its current sector."""

    def build(status: RequestStatus) -> CreditRequest:
        request = submit(customer)
        if status is RequestStatus.IN_REVIEW:
            return request
        if status is RequestStatus.RETURNED:
            workflow.transition(db, request, Action.RETURN, admin, T0 + HOUR, reason="missing")
        elif status is RequestStatus.APPROVED:
            for i in range(5):
                workflow.transition(db, request, Action.APPROVE, admin, T0 + HOUR * (i + 1))
        elif status is RequestStatus.REJECTED:
            workflow.transition(db, request, Action.REJECT, admin, T0 + HOUR, reason="no")
        elif status is RequestStatus.CANCELLED:
            workflow.transition(db, request, Action.CANCEL, customer, T0 + HOUR)
        elif status is RequestStatus.EXPIRED:
            workflow.apply_due_system_events(db, request, T0 + timedelta(days=46))
        db.commit()
        assert request.status is status
        return request

    return build


@pytest.mark.parametrize("actor_kind", ACTORS)
@pytest.mark.parametrize("action", list(SPEC))
@pytest.mark.parametrize("status", list(RequestStatus))
def test_every_status_action_actor_combination(
    db, customer, other_customer, make_employee, build_in_status, admin, status, action, actor_kind
):
    request = build_in_status(status)
    other_sector = db.scalar(select(Sector.id).where(Sector.id != request.current_sector_id))
    actors: dict[str, User] = {
        "owner": customer,
        "other_customer": other_customer,
        "sector_staff": make_employee(UserRole.STAFF, request.current_sector_id),
        "sector_manager": make_employee(UserRole.MANAGER, request.current_sector_id),
        "other_sector_staff": make_employee(UserRole.STAFF, other_sector),
        "admin": admin,
    }
    allowed_actors, allowed_statuses, event_type = SPEC[action]
    reason = "needs a reason"
    at = T0 + timedelta(days=50 if status is RequestStatus.EXPIRED else 0, hours=10)

    if actor_kind not in allowed_actors:
        with pytest.raises(workflow.Forbidden):
            workflow.transition(db, request, action, actors[actor_kind], at, reason=reason)
    elif status not in allowed_statuses:
        with pytest.raises(workflow.WorkflowError) as error:
            workflow.transition(db, request, action, actors[actor_kind], at, reason=reason)
        assert error.value.status_code == 409
    else:
        event = workflow.transition(db, request, action, actors[actor_kind], at, reason=reason)
        assert event.event_type is event_type
        assert event.actor_user_id == actors[actor_kind].id


def test_submit_requires_the_owning_customer(db, customer, other_customer, retail_staff):
    kwargs = {
        "amount": Decimal("10.00"),
        "purpose": "x",
        "term_days": 30,
        "deliver_date": (T0 + timedelta(days=5)).date(),
        "documents": REQUIRED_DOCUMENTS,
    }
    with pytest.raises(workflow.Forbidden):
        workflow.submit_request(db, customer.client, other_customer, T0, **kwargs)
    with pytest.raises(workflow.Forbidden):
        workflow.submit_request(db, customer.client, retail_staff, T0, **kwargs)
    with pytest.raises(workflow.InvalidAmount):
        workflow.submit_request(
            db, customer.client, customer, T0, **{**kwargs, "amount": Decimal(0)}
        )
    with pytest.raises(workflow.MissingDocuments, match="business_plan"):
        workflow.submit_request(
            db,
            customer.client,
            customer,
            T0,
            **{**kwargs, "documents": REQUIRED_DOCUMENTS - {DocumentType.BUSINESS_PLAN}},
        )
    with pytest.raises(workflow.InvalidDeliverDate):
        workflow.submit_request(
            db,
            customer.client,
            customer,
            T0,
            **{**kwargs, "deliver_date": (T0 - timedelta(days=1)).date()},
        )


# --- Scenarios ---


def test_five_stage_happy_path(db, customer, submit, make_employee):
    request = submit(customer, "100000.00")
    expected = [
        ("document_check", "retail_center", 24),
        ("screening", "retail_center", 24),
        ("analysis", "retail_center", 72),
        ("instrument_drafting", "retail_center", 48),
        ("disbursement", "disbursement_center", 24),
    ]
    assert request.sla_due_at == T0 + 24 * HOUR
    now = T0
    for i, (stage, sector, hours) in enumerate(expected):
        assert request.current_stage.code == stage
        assert request.current_sector.code == sector
        assert request.sla_due_at == (T0 if i == 0 else now) + hours * HOUR
        staff = make_employee(UserRole.STAFF, request.current_sector_id)
        now += HOUR
        workflow.transition(db, request, Action.APPROVE, staff, now, expected_seq=request.last_seq)
        db.commit()
    assert request.status is RequestStatus.APPROVED
    assert request.closed_at == now
    assert request.sla_due_at is None
    events = events_of(db, request)
    assert [e.seq for e in events] == [1, 2, 3, 4, 5, 6]
    assert events[0].event_type is EventType.SUBMITTED
    assert events[-1].to_status is RequestStatus.APPROVED
    assert events[-1].stage_id == request.current_stage_id  # terminal events keep the last stage
    assert [n.subject for n in notifications_of(db, request)] == ["Solicitação de crédito aprovada"]


def test_large_amount_goes_through_the_mid_large_center(db, customer, submit, admin):
    request = submit(customer, "5000000.00")
    assert request.current_sector.code == "mid_large_center"
    assert request.sla_due_at == T0 + 48 * HOUR
    for i in range(4):
        workflow.transition(db, request, Action.APPROVE, admin, T0 + HOUR * (i + 1))
    assert request.current_stage.code == "disbursement"
    assert request.current_sector.code == "disbursement_center"


@pytest.mark.parametrize(
    ("amount", "sector"),
    [
        ("4799999.99", "retail_center"),
        ("4800000.00", "mid_large_center"),
        ("0.01", "retail_center"),
    ],
)
def test_band_boundary(customer, submit, amount, sector):
    assert submit(customer, amount).current_sector.code == sector


def test_return_then_resubmit_re_enters_the_same_stage(db, customer, submit, retail_staff):
    request = submit(customer)
    workflow.transition(db, request, Action.APPROVE, retail_staff, T0 + HOUR)  # now in screening
    with pytest.raises(workflow.ReasonRequired):
        workflow.transition(db, request, Action.RETURN, retail_staff, T0 + 2 * HOUR, reason="  ")
    returned = workflow.transition(
        db, request, Action.RETURN, retail_staff, T0 + 2 * HOUR, reason="Missing statement"
    )
    assert request.status is RequestStatus.RETURNED
    assert request.sla_due_at is None
    assert returned.reason == "Missing statement"
    assert workflow.allowed_actions(request, customer, T0 + 3 * HOUR) == [
        Action.RESUBMIT,
        Action.CANCEL,
    ]

    workflow.transition(db, request, Action.RESUBMIT, customer, T0 + 5 * HOUR)
    assert request.status is RequestStatus.IN_REVIEW
    assert request.current_stage.code == "screening"
    assert request.sla_due_at == T0 + 5 * HOUR + 24 * HOUR
    assert request.stage_entered_at == T0 + 5 * HOUR
    assert [n.subject for n in notifications_of(db, request)] == [
        "Solicitação de crédito devolvida"
    ]


def test_cancel_closes_without_notifying(db, customer, submit):
    request = submit(customer)
    workflow.transition(db, request, Action.CANCEL, customer, T0 + HOUR)
    assert request.status is RequestStatus.CANCELLED
    assert request.closed_at == T0 + HOUR
    assert notifications_of(db, request) == []
    with pytest.raises(workflow.InvalidTransition):
        workflow.transition(db, request, Action.CANCEL, customer, T0 + 2 * HOUR)


def test_stale_expected_seq(db, customer, submit, retail_staff):
    request = submit(customer)
    with pytest.raises(workflow.StaleSequence):
        workflow.transition(
            db, request, Action.APPROVE, retail_staff, T0 + HOUR, expected_seq=request.last_seq + 1
        )


def test_lazy_expiry_writes_the_events_and_raises(db, customer, submit, admin):
    request = submit(customer)
    expires_at = T0 + timedelta(days=45)
    with pytest.raises(workflow.RequestExpired):
        workflow.transition(db, request, Action.APPROVE, admin, expires_at + HOUR)
    db.commit()
    assert request.status is RequestStatus.EXPIRED
    assert request.closed_at == expires_at
    events = events_of(db, request)
    assert [e.event_type for e in events] == [
        EventType.SUBMITTED,
        EventType.SLA_BREACHED,
        EventType.EXPIRED,
    ]
    assert events[1].occurred_at == T0 + 24 * HOUR  # the deadline, not the run time
    assert events[2].occurred_at == expires_at
    assert events[2].actor_user_id is None
    assert [n.subject for n in notifications_of(db, request)] == ["Solicitação de crédito expirada"]
    assert workflow.allowed_actions(request, admin, expires_at + HOUR) == []


def test_returned_requests_expire_too(db, customer, submit, retail_staff):
    request = submit(customer)
    workflow.transition(db, request, Action.RETURN, retail_staff, T0 + HOUR, reason="docs")
    with pytest.raises(workflow.RequestExpired):
        workflow.transition(db, request, Action.RESUBMIT, customer, T0 + timedelta(days=45))
    assert request.status is RequestStatus.EXPIRED


def test_action_just_before_expiry_still_works(db, customer, submit, retail_staff):
    request = submit(customer)
    just_before = T0 + timedelta(days=45) - timedelta(seconds=1)
    workflow.transition(db, request, Action.APPROVE, retail_staff, just_before)
    assert request.status is RequestStatus.IN_REVIEW
    # the late approval also recorded the SLA breach that happened on the way
    types = [e.event_type for e in events_of(db, request)]
    assert types == [EventType.SUBMITTED, EventType.SLA_BREACHED, EventType.STAGE_APPROVED]


def test_clock_going_backwards_raises(db, customer, submit, retail_staff):
    request = submit(customer)
    workflow.transition(db, request, Action.APPROVE, retail_staff, T0 + 2 * HOUR)
    staff = retail_staff
    with pytest.raises(workflow.ClockWentBackwards):
        workflow.transition(db, request, Action.APPROVE, staff, T0 + HOUR)


def test_naive_time_is_rejected(db, customer, submit, retail_staff):
    request = submit(customer)
    with pytest.raises(ValueError, match="timezone-aware"):
        workflow.transition(db, request, Action.APPROVE, retail_staff, T0.replace(tzinfo=None))


def test_events_are_append_only_in_the_orm(db, customer, submit):
    request = submit(customer)
    event = events_of(db, request)[0]
    event.reason = "tampered"
    with pytest.raises(AppendOnlyViolation):
        db.flush()
    db.rollback()
    db.delete(events_of(db, request)[0])
    with pytest.raises(AppendOnlyViolation):
        db.flush()
    db.rollback()
    assert len(events_of(db, request)) == 1


# --- System events and replay ---


def test_apply_due_system_events_is_idempotent(db, customer, submit):
    request = submit(customer)
    job = JobRun(job_name="sla-check", status=JobStatus.RUNNING, params={}, started_at=T0)
    db.add(job)
    db.flush()
    late = T0 + timedelta(days=50)

    first = workflow.apply_due_system_events(db, request, late, job_run_id=job.run_id)
    assert [e.event_type for e in first] == [EventType.SLA_BREACHED, EventType.EXPIRED]
    assert all(e.job_run_id == job.run_id for e in first)
    db.commit()
    count = db.scalar(select(func.count()).select_from(RequestEvent))

    assert workflow.apply_due_system_events(db, request, late, job_run_id=job.run_id) == []
    assert workflow.apply_due_system_events(db, request, late + HOUR) == []
    db.commit()
    assert db.scalar(select(func.count()).select_from(RequestEvent)) == count


def test_breach_alone_is_recorded_once_and_cleared_on_the_next_stage(
    db, customer, submit, retail_staff
):
    request = submit(customer)
    due = T0 + 24 * HOUR
    assert workflow.apply_due_system_events(db, request, due - HOUR) == []
    [breach] = workflow.apply_due_system_events(db, request, due + HOUR)
    assert breach.event_type is EventType.SLA_BREACHED
    assert breach.occurred_at == due
    assert request.sla_breached_at == due
    assert request.status is RequestStatus.IN_REVIEW
    assert notifications_of(db, request) == []  # breaches are internal
    workflow.transition(db, request, Action.APPROVE, retail_staff, due + 2 * HOUR)
    assert request.sla_breached_at is None


def test_replay_equals_the_projection(db, customer, submit, retail_staff, admin):
    request = submit(customer)
    workflow.apply_due_system_events(db, request, T0 + 25 * HOUR)  # breach
    workflow.transition(db, request, Action.APPROVE, retail_staff, T0 + 26 * HOUR)
    workflow.transition(db, request, Action.RETURN, retail_staff, T0 + 27 * HOUR, reason="docs")
    workflow.transition(db, request, Action.RESUBMIT, customer, T0 + 28 * HOUR)
    workflow.transition(db, request, Action.APPROVE, retail_staff, T0 + 29 * HOUR)
    db.commit()
    assert workflow.replay(events_of(db, request)) == workflow.state_of(request)

    workflow.apply_due_system_events(db, request, T0 + timedelta(days=60))
    db.commit()
    state = workflow.replay(events_of(db, request))
    assert state == workflow.state_of(request)
    assert state.status is RequestStatus.EXPIRED


def test_replay_matches_for_every_terminal_path(db, customer, submit, admin, build_in_status):
    for status in (RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED):
        request = build_in_status(status)
        assert workflow.replay(events_of(db, request)) == workflow.state_of(request)


def test_estimated_completion_adds_the_remaining_stages(db, customer, submit):
    retail = submit(customer, "100000.00")
    assert (
        workflow.estimated_completion_at(db, retail)
        == retail.sla_due_at + (24 + 72 + 48 + 24) * HOUR
    )
    large = submit(customer, "5000000.00")
    assert (
        workflow.estimated_completion_at(db, large)
        == large.sla_due_at + (48 + 120 + 72 + 24) * HOUR
    )
