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
from bank_credit.app.database import Base, engine

# Association table: which sectors approve which processes
sector_approval = Table(
    "sector_approval",
    Base.metadata,
    Column("sector_id", Integer, ForeignKey("sectors.id")),
    Column("process_id", Integer, ForeignKey("processes.id")),
)

# Association table for user-group membership
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("group_id", Integer, ForeignKey("groups.id")),
)

# Association table for group-sector membership
sector_groups = Table(
    "sector_groups",
    Base.metadata,
    Column("sector_id", Integer, ForeignKey("sectors.id")),
    Column("group_id", Integer, ForeignKey("groups.id")),
)


class User(Base):
    def __str__(self):
        return f"User {self.id} - {self.full_name} - {self.email}"
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    # Many-to-many: users <-> groups
    groups = relationship("Group", secondary="user_groups", back_populates="users")
    # One-to-one: user <-> client/employee
    client = relationship("Client", uselist=False, back_populates="user")
    employee = relationship("Employee", uselist=False, back_populates="user")

    @property
    def is_client(self):
        return self.client is not None

    @property
    def is_employee(self):
        return self.employee is not None
class Client(Base):
    def __str__(self):
        return f"Client {self.id} - {self.nome_fantasia} - {self.cnpj} - ({self.user})"
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    cnpj = Column(String, unique=True, index=True)
    nome_fantasia = Column(String)
    razao_social = Column(String)
    cnae_principal = Column(String)
    cnae_principal_desc = Column(String)
    cnae_secundario = Column(String)
    cnae_secundario_desc = Column(String)
    natureza_juridica = Column(String)
    natureza_juridica_desc = Column(String)
    logradouro = Column(String)
    numero = Column(String)
    complemento = Column(String)
    cep = Column(String)
    bairro = Column(String)
    municipio = Column(String)
    uf = Column(String)
    # Removido: notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")
    credit_requests = relationship("CreditRequest", back_populates="client")
    user = relationship("User", back_populates="client")


class Employee(Base):
    def __str__(self):
        return f"Employee {self.id} - {self.matricula} - {self.cpf} - ({self.user})"
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    matricula = Column(String, unique=True, index=True)
    cpf = Column(String, unique=True, index=True)
    user = relationship("User", back_populates="employee")
    # One-to-many: employee can be manager of sectors
    managed_sectors = relationship("Sector", back_populates="manager")


class Group(Base):
    def __str__(self):
        return f"Group {self.id} - {self.name}"
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary="user_groups", back_populates="groups")
    sectors = relationship("Sector", secondary="sector_groups", back_populates="groups")


class Sector(Base):
    def __str__(self):
        return f"Sector {self.id} - {self.name} - ({self.manager})"
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    limit = Column(Float)
    sla_days = Column(Integer)
    require_all = Column(Boolean, default=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=True)
    manager = relationship("Employee", back_populates="managed_sectors")
    groups = relationship("Group", secondary="sector_groups", back_populates="sectors")
    processes = relationship("Process", secondary=sector_approval, back_populates="sectors")


class Process(Base):
    def __str__(self):
        return f"Process {self.id} - {self.name} - ({self.next_process})"
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    next_process_id = Column(Integer, ForeignKey("processes.id"), nullable=True)

    # Self-referential relationship for process sequence
    next_process = relationship("Process", remote_side=[id])

    # Sectors that must approve this process
    sectors = relationship("Sector", secondary=sector_approval, back_populates="processes")


class CreditRequest(Base):
    def __str__(self):
        return f"CreditRequest {self.id} - {self.client} - {self.amount} - {self.status}"
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
    def __str__(self):
        return f"RequestHistory {self.id} - {self.request_id} - {self.status} - {self.timestamp} - {self.reason}"
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("credit_requests.id"))
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(String, nullable=True)  # Novo campo para motivo da recusa

    # Relationship back to the credit request
    request = relationship("CreditRequest", back_populates="history")


class Notification(Base):
    def __str__(self):
        return f"Notification {self.id} - {self.client_id} - {self.subject} - {self.read}"
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Removido: client = relationship("Client", back_populates="notifications")
    client = relationship("Client")
