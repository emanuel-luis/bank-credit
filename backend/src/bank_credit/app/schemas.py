"""API schemas. Inputs forbid unknown fields; money is Decimal and serializes as a string."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from bank_credit.app.domain.documents import Cnpj
from bank_credit.app.domain.enums import Action, DocumentType, EventType, RequestStatus, UserRole

Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2, gt=0)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Authentication and registration ---


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(Input):
    # Public registration input: role, is_superuser, groups and the like are rejected.
    email: EmailStr
    full_name: Annotated[Text, Field(max_length=200)]
    phone: Annotated[Text, Field(max_length=20)]
    password: Annotated[str, Field(min_length=8, max_length=128)]


class ClientCreate(Input):
    cnpj: Cnpj
    trade_name: Annotated[Text, Field(max_length=200)]
    legal_name: Annotated[Text, Field(max_length=200)]
    cnae_primary: Annotated[Text, Field(max_length=16)]
    cnae_primary_desc: Annotated[Text, Field(max_length=255)]
    cnae_secondary: Annotated[str | None, Field(max_length=16)] = None
    cnae_secondary_desc: Annotated[str | None, Field(max_length=255)] = None
    legal_nature_code: Annotated[Text, Field(max_length=8)]
    legal_nature_desc: Annotated[Text, Field(max_length=255)]
    street: Annotated[Text, Field(max_length=200)]
    number: Annotated[Text, Field(max_length=20)]
    complement: Annotated[str | None, Field(max_length=100)] = None
    postal_code: Annotated[str, Field(pattern=r"^[0-9]{8}$")]
    district: Annotated[Text, Field(max_length=100)]
    city: Annotated[Text, Field(max_length=100)]
    state: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    user: UserCreate


class UserRead(Output):
    id: int
    email: str
    full_name: str
    phone: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class ClientRead(Output):
    id: int
    cnpj: str
    trade_name: str
    legal_name: str
    cnae_primary: str
    cnae_primary_desc: str
    cnae_secondary: str | None
    cnae_secondary_desc: str | None
    legal_nature_code: str
    legal_nature_desc: str
    street: str
    number: str
    complement: str | None
    postal_code: str
    district: str
    city: str
    state: str


class ClientWithUser(ClientRead):
    user: UserRead


class SectorRef(Output):
    code: str
    name: str


class StageRef(Output):
    code: str
    name: str
    position: int


class EmployeeRead(Output):
    id: int
    employee_number: str
    sector: SectorRef | None


class Me(UserRead):
    client: ClientRead | None
    employee: EmployeeRead | None


# --- Notifications ---


class NotificationRead(Output):
    id: int
    client_id: int
    request_id: int | None
    subject: str
    message: str
    read_at: datetime | None
    created_at: datetime


# --- Credit requests ---


class CreditRequestCreate(Input):
    amount: Money
    purpose: Annotated[Text, Field(max_length=500)]
    term_days: Annotated[int, Field(gt=0)]
    deliver_date: date
    documents: list[DocumentType]

    @field_validator("documents")
    @classmethod
    def _no_duplicates(cls, value: list[DocumentType]) -> list[DocumentType]:
        if len(set(value)) != len(value):
            raise ValueError("documents must not contain duplicates")
        return value


class TransitionIn(Input):
    action: Action
    reason: str | None = None
    expected_seq: int


class ClientSummary(Output):
    id: int
    cnpj: str
    trade_name: str
    legal_name: str


class RequestSummary(Output):
    id: int
    amount: Decimal
    purpose: str
    term_days: int
    deliver_date: date
    status: RequestStatus
    stage: StageRef
    sector: SectorRef
    submitted_at: datetime
    stage_entered_at: datetime
    sla_due_at: datetime | None
    is_overdue: bool
    closed_at: datetime | None
    client: ClientSummary


class DocumentRead(Output):
    document_type: DocumentType
    declared_at: datetime


class RequestDetail(RequestSummary):
    documents: list[DocumentRead]
    estimated_completion_at: datetime | None
    last_seq: int
    allowed_actions: list[Action]


class RequestPage(BaseModel):
    items: list[RequestSummary]
    total: int


class ActorRef(Output):
    id: int
    full_name: str
    role: UserRole


class HistoryItem(Output):
    seq: int
    event_type: EventType
    from_status: RequestStatus | None
    to_status: RequestStatus
    stage: StageRef
    sector: SectorRef
    actor: ActorRef | None
    reason: str | None
    occurred_at: datetime


class RouteRead(BaseModel):
    sector: SectorRef
    min_amount: Decimal
    max_amount: Decimal | None
    sla_hours: int


class StageWorkflow(StageRef):
    routes: list[RouteRead]


class WorkflowRead(BaseModel):
    stages: list[StageWorkflow]
