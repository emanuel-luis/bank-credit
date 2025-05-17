# app/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Table,
    Boolean,
    Text,
    Date,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from bank_credit.app.database import Base

# Association table: which sectors approve which processes
sector_approval = Table(
    "sector_approval",
    Base.metadata,
    Column("sector_id", Integer, ForeignKey("sectors.id")),
    Column("process_id", Integer, ForeignKey("processes.id")),
)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String, unique=True, index=True)
    full_name = Column(String)
    birth_date = Column(Date)
    phone = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # One-to-many relationship: one client can have many credit requests
    credit_requests = relationship("CreditRequest", back_populates="client")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")


class CreditRequest(Base):
    __tablename__ = "credit_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Float, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deliver_date = Column(DateTime, nullable=False)

    # Current process pointer
    current_process_id = Column(Integer, ForeignKey("processes.id"), nullable=True)

    # Relationships
    client = relationship("Client", back_populates="credit_requests")
    history = relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan")
    current_process = relationship("Process")


class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("credit_requests.id"))
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship back to the credit request
    request = relationship("CreditRequest", back_populates="history")


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    limit = Column(Float)  # Max amount this sector handles
    sla_days = Column(Integer)  # SLA in days
    require_all = Column(Boolean, default=False)

    # Processes this sector is involved in approving
    processes = relationship("Process", secondary=sector_approval, back_populates="sectors")


class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    next_process_id = Column(Integer, ForeignKey("processes.id"), nullable=True)

    # Self-referential relationship for process sequence
    next_process = relationship("Process", remote_side=[id])

    # Sectors that must approve this process
    sectors = relationship("Sector", secondary=sector_approval, back_populates="processes")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="notifications")
