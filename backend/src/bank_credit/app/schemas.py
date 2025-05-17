# app/schemas.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List

# --- Authentication models ---


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Client models ---


class ClientBase(BaseModel):
    username: str
    email: EmailStr


class ClientCreate(ClientBase):
    password: str


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
        if v <= datetime.utcnow():
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
