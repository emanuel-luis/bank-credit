"""ORM models. The schema is owned by Alembic; tests use create_all."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CHAR,
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    func,
    text,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from bank_credit.app.db import Base, enum_column
from bank_credit.app.domain.enums import (
    DocumentType,
    EventType,
    JobStatus,
    RequestStatus,
    UserRole,
)

_CLOSED = "('APPROVED','REJECTED','CANCELLED','EXPIRED')"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    hashed_password: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole, "role", 16))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    created_at: Mapped[datetime]
    last_login_at: Mapped[datetime | None]

    client: Mapped["Client | None"] = relationship(back_populates="user")
    employee: Mapped["Employee | None"] = relationship(back_populates="user")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("length(cnpj) = 14", name="cnpj_length"),
        CheckConstraint("cnpj ~ '^[0-9A-Z]{12}[0-9]{2}$'", name="cnpj_format").ddl_if(
            dialect="postgresql"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    cnpj: Mapped[str] = mapped_column(CHAR(14), unique=True)
    trade_name: Mapped[str] = mapped_column(String(200))
    legal_name: Mapped[str] = mapped_column(String(200))
    cnae_primary: Mapped[str] = mapped_column(String(16))
    cnae_primary_desc: Mapped[str] = mapped_column(String(255))
    cnae_secondary: Mapped[str | None] = mapped_column(String(16))
    cnae_secondary_desc: Mapped[str | None] = mapped_column(String(255))
    legal_nature_code: Mapped[str] = mapped_column(String(8))
    legal_nature_desc: Mapped[str] = mapped_column(String(255))
    street: Mapped[str] = mapped_column(String(200))
    number: Mapped[str] = mapped_column(String(20))
    complement: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(CHAR(8))
    district: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(CHAR(2))

    user: Mapped[User] = relationship(back_populates="client")
    credit_requests: Mapped[list["CreditRequest"]] = relationship(back_populates="client")


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("length(cpf) = 11", name="cpf_length"),
        CheckConstraint("cpf ~ '^[0-9]{11}$'", name="cpf_format").ddl_if(dialect="postgresql"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    employee_number: Mapped[str] = mapped_column(String(16), unique=True)
    cpf: Mapped[str] = mapped_column(CHAR(11), unique=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"))

    user: Mapped[User] = relationship(back_populates="employee")
    sector: Mapped[Sector | None] = relationship()


class Stage(Base):
    __tablename__ = "stages"
    __table_args__ = (CheckConstraint("position > 0", name="position_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(SmallInteger, unique=True)


class StageRoute(Base):
    __tablename__ = "stage_routes"
    __table_args__ = (
        UniqueConstraint("stage_id", "min_amount"),
        CheckConstraint("sla_hours > 0", name="sla_hours_positive"),
        CheckConstraint("max_amount is null or max_amount > min_amount", name="band_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id", ondelete="RESTRICT"))
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"))
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal(0), server_default=text("0")
    )
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sla_hours: Mapped[int] = mapped_column(Integer)

    stage: Mapped[Stage] = relationship()
    sector: Mapped[Sector] = relationship()


class JobRun(Base):
    __tablename__ = "job_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_name: Mapped[str] = mapped_column(String(32))
    status: Mapped[JobStatus] = mapped_column(enum_column(JobStatus, "status", 16))
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    started_at: Mapped[datetime]
    finished_at: Mapped[datetime | None]
    rows_read: Mapped[int | None]
    rows_written: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)


class CreditRequest(Base):
    __tablename__ = "credit_requests"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("term_days > 0", name="term_days_positive"),
        CheckConstraint(f"(status in {_CLOSED}) = (closed_at is not null)", name="closed_at_state"),
        Index("ix_credit_requests_current_sector_id", "current_sector_id", "status", "sla_due_at"),
        Index("ix_credit_requests_client_id", "client_id", "submitted_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    purpose: Mapped[str] = mapped_column(String(500))
    term_days: Mapped[int]
    deliver_date: Mapped[date] = mapped_column(Date)
    status: Mapped[RequestStatus] = mapped_column(enum_column(RequestStatus, "status", 16))
    current_stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id", ondelete="RESTRICT"))
    current_sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"))
    submitted_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    stage_entered_at: Mapped[datetime]
    sla_due_at: Mapped[datetime | None]
    sla_breached_at: Mapped[datetime | None]
    closed_at: Mapped[datetime | None]
    last_seq: Mapped[int]
    updated_at: Mapped[datetime]

    client: Mapped[Client] = relationship(back_populates="credit_requests")
    current_stage: Mapped[Stage] = relationship()
    current_sector: Mapped[Sector] = relationship()
    documents: Mapped[list["RequestDocument"]] = relationship(
        back_populates="request", order_by="RequestDocument.document_type"
    )


class RequestDocument(Base):
    """A document the customer declared for a request. No file is stored."""

    __tablename__ = "request_documents"

    request_id: Mapped[int] = mapped_column(
        ForeignKey("credit_requests.id", ondelete="RESTRICT"), primary_key=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        enum_column(DocumentType, "document_type", 24), primary_key=True
    )
    declared_at: Mapped[datetime]

    request: Mapped[CreditRequest] = relationship(back_populates="documents")


class RequestEvent(Base):
    """Append-only event log: the source of truth for a request's state."""

    __tablename__ = "request_events"
    __table_args__ = (
        UniqueConstraint("request_id", "seq"),
        CheckConstraint(
            "event_type not in ('RETURNED','REJECTED') or reason is not null",
            name="reason_required",
        ),
        Index("ix_request_events_occurred_at", "occurred_at"),
        Index("ix_request_events_stage_id", "stage_id", "sector_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), Identity(), primary_key=True
    )
    request_id: Mapped[int] = mapped_column(ForeignKey("credit_requests.id", ondelete="RESTRICT"))
    seq: Mapped[int]
    event_type: Mapped[EventType] = mapped_column(enum_column(EventType, "event_type", 24))
    from_status: Mapped[RequestStatus | None] = mapped_column(
        enum_column(RequestStatus, "from_status", 16)
    )
    to_status: Mapped[RequestStatus] = mapped_column(enum_column(RequestStatus, "to_status", 16))
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id", ondelete="RESTRICT"))
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"))
    sla_due_at: Mapped[datetime | None]
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    job_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("job_runs.run_id", ondelete="RESTRICT")
    )
    reason: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime]
    recorded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    stage: Mapped[Stage] = relationship()
    sector: Mapped[Sector] = relationship()
    actor: Mapped[User | None] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_client_id", "client_id", "read_at", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("credit_requests.id", ondelete="RESTRICT")
    )
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None]
    created_at: Mapped[datetime]


class AppendOnlyViolation(RuntimeError):
    """Raised when code tries to update or delete a request event."""


@event.listens_for(Session, "before_flush")
def _guard_request_events(session: Session, _ctx: object, _instances: object) -> None:
    for obj in session.dirty:
        if isinstance(obj, RequestEvent) and session.is_modified(obj):
            raise AppendOnlyViolation("request_events rows cannot be updated")
    for obj in session.deleted:
        if isinstance(obj, RequestEvent):
            raise AppendOnlyViolation("request_events rows cannot be deleted")
