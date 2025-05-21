# app/schemas.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
import re

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
    manager_id: Optional[int] = None


class Sector(SectorBase):
    id: int
    groups: Optional[List[Group]] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str


class UserCreate(UserBase):
    password: str
    is_superuser: Optional[bool] = False
    groups: Optional[List[str]] = []


class ClientBase(BaseModel):
    cnpj: str
    nome_fantasia: str
    razao_social: str
    cnae_principal: str
    cnae_principal_desc: str
    cnae_secundario: Optional[str] = None
    cnae_secundario_desc: Optional[str] = None
    natureza_juridica: str
    natureza_juridica_desc: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
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
    checklist: Optional[List[bool]] = []



class CreditRequestCreate(CreditRequestBase):
    pass


class CreditRequest(CreditRequestBase):
    id: int
    client_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    current_process_id: Optional[int] = None


# --- Request History Schemas ---


class RequestHistoryBase(BaseModel):
    status: str
    timestamp: datetime
    reason: Optional[str] = None  # Novo campo para motivo


class RequestHistory(RequestHistoryBase):
    id: int
    request_id: int


# --- Process Schemas ---


class ProcessBase(BaseModel):
    name: str


class Process(ProcessBase):
    id: int
    next_process_id: Optional[int] = None


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    is_client: bool = False
    is_employee: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    groups: Optional[List[Group]] = []
    role: str | None = None
    client: Client | None = None
    employee: Employee | None = None

    class Config:
        from_attributes = True


# Resolve forward references
CreditRequest.model_rebuild()
