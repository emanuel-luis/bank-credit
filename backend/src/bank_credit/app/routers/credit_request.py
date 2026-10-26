"""Credit requests: list, detail, history, submission, workflow transitions and the workflow map."""

import logging
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from bank_credit.app import schemas
from bank_credit.app.db import get_db
from bank_credit.app.deps import get_now
from bank_credit.app.domain import workflow
from bank_credit.app.domain.enums import RequestStatus, UserRole
from bank_credit.app.errors import ApiError
from bank_credit.app.models import CreditRequest, RequestEvent, Stage, StageRoute, User
from bank_credit.app.routers.auth import get_current_active_user

logger = logging.getLogger("bank_credit.routers.credit_request")

router = APIRouter()


class Scope(StrEnum):
    MINE = "mine"
    QUEUE = "queue"
    ALL = "all"


# Each role sees exactly one scope.
_ROLE_SCOPE = {
    UserRole.CUSTOMER: Scope.MINE,
    UserRole.STAFF: Scope.QUEUE,
    UserRole.MANAGER: Scope.QUEUE,
    UserRole.ADMIN: Scope.ALL,
}


def _summary(request: CreditRequest, now: datetime) -> schemas.RequestSummary:
    overdue = (
        request.status is RequestStatus.IN_REVIEW
        and request.sla_due_at is not None
        and now >= request.sla_due_at
    )
    return schemas.RequestSummary(
        id=request.id,
        amount=request.amount,
        purpose=request.purpose,
        term_days=request.term_days,
        deliver_date=request.deliver_date,
        status=request.status,
        stage=schemas.StageRef.model_validate(request.current_stage),
        sector=schemas.SectorRef.model_validate(request.current_sector),
        submitted_at=request.submitted_at,
        stage_entered_at=request.stage_entered_at,
        sla_due_at=request.sla_due_at,
        is_overdue=overdue,
        closed_at=request.closed_at,
        client=schemas.ClientSummary.model_validate(request.client),
    )


def _detail(
    db: Session, request: CreditRequest, user: User, now: datetime
) -> schemas.RequestDetail:
    return schemas.RequestDetail(
        **dict(_summary(request, now)),
        estimated_completion_at=workflow.estimated_completion_at(db, request),
        last_seq=request.last_seq,
        allowed_actions=workflow.allowed_actions(request, user, now),
    )


def _get_visible(db: Session, request_id: int, user: User) -> CreditRequest:
    """Customers see only their own requests; employees see every request."""
    request = db.get(CreditRequest, request_id)
    owned = user.client is not None and request is not None and request.client_id == user.client.id
    if request is None or (user.role is UserRole.CUSTOMER and not owned):
        raise ApiError(status.HTTP_404_NOT_FOUND, "Request not found", "request_not_found")
    return request


def _scoped(
    query: Select[tuple[CreditRequest]], scope: Scope, user: User
) -> Select[tuple[CreditRequest]]:
    if scope is Scope.MINE:
        return query.where(CreditRequest.client_id == (user.client.id if user.client else -1))
    if scope is Scope.QUEUE:
        sector_id = user.employee.sector_id if user.employee else None
        return query.where(CreditRequest.current_sector_id == sector_id)
    return query


@router.get("", response_model=schemas.RequestPage)
def list_requests(
    scope: Scope | None = None,
    status_filter: Annotated[RequestStatus | None, Query(alias="status")] = None,
    stage: str | None = None,
    overdue: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> schemas.RequestPage:
    allowed = _ROLE_SCOPE[user.role]
    if scope is not None and scope is not allowed:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            f"Scope {scope.value} is not allowed for your role",
            "scope_not_allowed",
        )
    if allowed is Scope.QUEUE and status_filter is None:
        status_filter = RequestStatus.IN_REVIEW  # a sector's queue is its open work by default

    filtered = _scoped(select(CreditRequest), allowed, user)
    if status_filter is not None:
        filtered = filtered.where(CreditRequest.status == status_filter)
    if stage is not None:
        filtered = filtered.join(Stage, Stage.id == CreditRequest.current_stage_id).where(
            Stage.code == stage
        )
    if overdue is not None:
        is_overdue = (CreditRequest.status == RequestStatus.IN_REVIEW) & (
            CreditRequest.sla_due_at <= now
        )
        filtered = filtered.where(is_overdue if overdue else ~is_overdue)

    total = db.scalar(select(func.count()).select_from(filtered.order_by(None).subquery())) or 0
    order = (
        (CreditRequest.sla_due_at.asc(), CreditRequest.id)
        if allowed is Scope.QUEUE
        else (CreditRequest.submitted_at.desc(), CreditRequest.id.desc())
    )
    rows = db.scalars(
        filtered.options(
            selectinload(CreditRequest.current_stage),
            selectinload(CreditRequest.current_sector),
            selectinload(CreditRequest.client),
        )
        .order_by(*order)
        .limit(limit)
        .offset(offset)
    )
    return schemas.RequestPage(items=[_summary(r, now) for r in rows], total=total)


@router.get("/{request_id}", response_model=schemas.RequestDetail)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> schemas.RequestDetail:
    return _detail(db, _get_visible(db, request_id, user), user, now)


@router.get("/{request_id}/history", response_model=list[schemas.HistoryItem])
def get_history(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> list[RequestEvent]:
    request = _get_visible(db, request_id, user)
    query = (
        select(RequestEvent)
        .where(RequestEvent.request_id == request.id)
        .options(
            selectinload(RequestEvent.stage),
            selectinload(RequestEvent.sector),
            selectinload(RequestEvent.actor),
        )
        .order_by(RequestEvent.seq)
    )
    return list(db.scalars(query))


@router.post("", response_model=schemas.RequestDetail, status_code=status.HTTP_201_CREATED)
def create_request(
    body: schemas.CreditRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> schemas.RequestDetail:
    if user.client is None:
        raise ApiError(
            status.HTTP_403_FORBIDDEN, "Only customers can submit requests", "customers_only"
        )
    request = workflow.submit_request(
        db,
        user.client,
        user,
        now,
        amount=body.amount,
        purpose=body.purpose,
        term_days=body.term_days,
        deliver_date=body.deliver_date,
    )
    db.commit()
    logger.info("Request %s submitted by user %s", request.id, user.id)
    return _detail(db, request, user, now)


@router.post("/{request_id}/transitions", response_model=schemas.RequestDetail)
def post_transition(
    request_id: int,
    body: schemas.TransitionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    now: datetime = Depends(get_now),
) -> schemas.RequestDetail:
    request = _get_visible(db, request_id, user)
    try:
        workflow.transition(
            db,
            request,
            body.action,
            user,
            now,
            reason=body.reason,
            expected_seq=body.expected_seq,
        )
    except workflow.RequestExpired:
        db.commit()  # keep the lazy EXPIRED event; the error is still reported
        raise
    db.commit()
    logger.info("Request %s: %s by user %s", request.id, body.action.value, user.id)
    return _detail(db, request, user, now)


workflow_router = APIRouter()


@workflow_router.get("/workflow", response_model=schemas.WorkflowRead)
def get_workflow(
    db: Session = Depends(get_db), _user: User = Depends(get_current_active_user)
) -> schemas.WorkflowRead:
    stages = db.scalars(select(Stage).order_by(Stage.position))
    routes = db.scalars(
        select(StageRoute)
        .options(selectinload(StageRoute.sector))
        .order_by(StageRoute.stage_id, StageRoute.min_amount)
    ).all()
    return schemas.WorkflowRead(
        stages=[
            schemas.StageWorkflow(
                code=stage.code,
                name=stage.name,
                position=stage.position,
                routes=[
                    schemas.RouteRead(
                        sector=schemas.SectorRef.model_validate(r.sector),
                        min_amount=r.min_amount,
                        max_amount=r.max_amount,
                        sla_hours=r.sla_hours,
                    )
                    for r in routes
                    if r.stage_id == stage.id
                ],
            )
            for stage in stages
        ]
    )
