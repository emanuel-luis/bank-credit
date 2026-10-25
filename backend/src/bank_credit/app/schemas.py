# app/schemas.py

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# --- Authentication models ---


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Client models ---


class GroupBase(BaseModel):
    name: str


class Group(GroupBase):
    id: int

    class Config:
        from_attributes = True


class SectorBase(BaseModel):
    name: str
    limit: float
    sla_days: int
    require_all: bool
    manager_id: int | None = None


class Sector(SectorBase):
    id: int
    groups: list[Group] | None = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str


class UserCreate(UserBase):
    password: str
    is_superuser: bool | None = False
    groups: list[str] | None = []


class ClientBase(BaseModel):
    cnpj: str
    nome_fantasia: str
    razao_social: str
    cnae_principal: str
    cnae_principal_desc: str
    cnae_secundario: str | None = None
    cnae_secundario_desc: str | None = None
    natureza_juridica: str
    natureza_juridica_desc: str
    logradouro: str
    numero: str
    complemento: str | None = None
    cep: str
    bairro: str
    municipio: str
    uf: str


class ClientCreate(ClientBase):
    user: UserCreate


class Client(ClientBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class ClientUser(ClientBase):
    user: User

    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    matricula: str
    cpf: str


class EmployeeCreate(EmployeeBase):
    user: UserCreate


class Employee(EmployeeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class EmployeeUser(EmployeeBase):
    id: int
    user: User

    class Config:
        from_attributes = True


# --- Notification Schemas ---


class NotificationCount(BaseModel):
    count: int


class NotificationBase(BaseModel):
    subject: str
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    client_id: int
    read: bool
    created_at: datetime


# --- Credit request models ---


class CreditRequestBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    deliver_date: datetime
    term: int
    purpose: str
    checklist: list[bool] | None = []


class CreditRequestCreate(CreditRequestBase):
    @field_validator("deliver_date")
    @classmethod
    def deliver_date_not_in_past(cls, value: datetime) -> datetime:
        now = datetime.now(value.tzinfo)
        if value < now:
            raise ValueError("deliver_date must not be in the past")
        return value


class CreditRequest(CreditRequestBase):
    id: int
    client: ClientUser
    client_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    current_process_id: int | None = None


# --- Request History Schemas ---


class RequestHistoryBase(BaseModel):
    status: str
    timestamp: datetime
    reason: str | None = None  # Novo campo para motivo


class RequestHistory(RequestHistoryBase):
    id: int
    request_id: int


# --- Process Schemas ---


class ProcessBase(BaseModel):
    name: str


class Process(ProcessBase):
    id: int
    next_process_id: int | None = None


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    is_client: bool = False
    is_employee: bool = False
    created_at: datetime
    last_login: datetime | None = None
    groups: list[Group] | None = []
    role: str | None = None
    client: Client | None = None
    employee: Employee | None = None

    class Config:
        from_attributes = True


# Resolve forward references
CreditRequest.model_rebuild()
