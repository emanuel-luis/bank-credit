# app/schemas.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime, UTC
from typing import Optional, List
import re

# --- Authentication models ---


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Client models ---


class ClientBase(BaseModel):
    email: EmailStr


class ClientCreate(BaseModel):
    cnpj: str
    full_name: str
    birth_date: date
    phone: str
    email: EmailStr
    password: str

    @validator("cnpj")
    def validate_cnpj(cls, v):
        cnpj = re.sub(r"\D", "", v)
        if not cnpj.isdigit():
            raise ValueError("CNPJ deve conter apenas números")
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            raise ValueError("CNPJ inválido")

        def calc(x):
            n = cnpj[:x]
            y = x - 7
            s = 0
            for i in range(x, 0, -1):
                s += int(n[x - i]) * y
                y -= 1
                if y < 2:
                    y = 9
            r = 11 - s % 11
            return 0 if r > 9 else r

        if not (calc(12) == int(cnpj[12]) and calc(13) == int(cnpj[13])):
            raise ValueError("CNPJ inválido")
        return cnpj

    @validator("full_name")
    def validate_full_name(cls, v):
        if len(v.strip().split(" ")) < 2:
            raise ValueError("Informe o nome completo")
        return v

    @validator("phone")
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Telefone deve conter apenas números")
        if len(v) < 10 or len(v) > 11:
            raise ValueError("Telefone deve ter entre 10 e 11 dígitos, incluindo DDD")
        return v

    @validator("birth_date")
    def validate_birth_date(cls, v):
        # Simples: só checa se não está vazio
        if not v:
            raise ValueError("Data de nascimento obrigatória")
        return v


class Client(ClientBase):
    id: int
    is_active: bool


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

    @validator("deliver_date")
    def validate_deliver_date(cls, v):
        if v <= datetime.now():
            raise ValueError("Deliver date must be in the future")
        return v


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


class RequestHistory(RequestHistoryBase):
    id: int
    request_id: int


# --- Process Schemas ---


class ProcessBase(BaseModel):
    name: str


class Process(ProcessBase):
    id: int
    next_process_id: Optional[int] = None


# --- Sector Schemas ---


class SectorBase(BaseModel):
    name: str
    limit: float
    sla_days: int
    require_all: bool


class Sector(SectorBase):
    id: int


# Resolve forward references
CreditRequest.model_rebuild()
