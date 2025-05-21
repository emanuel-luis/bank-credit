from typing import Optional
from sqlalchemy.orm import Session
from bank_credit.app import models, schemas
from datetime import datetime
from passlib.context import CryptContext
import logging

logger = logging.getLogger("bank_credit.views.auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug(f"[verify_password] Verificando senha para usuário.")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"[verify_password] Resultado: {result}")
    return result

def get_password_hash(password: str) -> str:
    logger.debug(f"[get_password_hash] Gerando hash para senha.")
    hash_ = pwd_context.hash(password)
    logger.debug(f"[get_password_hash] Hash gerado.")
    return hash_

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    logger.debug(f"Buscando usuário por email: {email}")
    user = db.query(models.User).filter(models.User.email == email).first()
    logger.debug(f"Resultado: {user}")
    return user

def get_client_by_email(db: Session, email: str) -> Optional[models.Client]:
    logger.debug(f"Buscando cliente por email: {email}")
    user = get_user_by_email(db, email)
    if not user:
        logger.debug("Usuário não encontrado para o email informado")
        return None
    client = db.query(models.Client).filter(models.Client.user_id == user.id).first()
    logger.debug(f"Resultado: {client}")
    return client

def get_employee_by_email(db: Session, email: str) -> Optional[models.Employee]:
    logger.debug(f"Buscando funcionário por email: {email}")
    user = get_user_by_email(db, email)
    if not user:
        logger.debug("Usuário não encontrado para o email informado")
        return None
    employee = db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
    logger.debug(f"Resultado: {employee}")
    return employee

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    logger.info(f"Criando usuário: {user_in.email}")
    db_user = models.User(
        full_name=user_in.full_name,
        phone=user_in.phone,
        email=user_in.email,
        hashed_password=user_in.password,
        is_active=True,
        is_superuser=user_in.is_superuser or False,
        created_at=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.debug(f"Usuário criado: {db_user}")
    if user_in.groups:
        for group_name in user_in.groups:
            group = db.query(models.Group).filter_by(name=group_name).first()
            if group:
                db_user.groups.append(group)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Usuário {db_user.id} salvo com grupos")
    return db_user

def create_client(db: Session, client_in: schemas.ClientCreate) -> models.Client:
    logger.info(f"Criando cliente para usuário: {client_in.user.email}")
    db_user = create_user(db, client_in.user)
    db_client = models.Client(
        user_id=db_user.id,
        cnpj=client_in.cnpj,
        nome_fantasia=client_in.nome_fantasia,
        razao_social=client_in.razao_social,
        cnae_principal=client_in.cnae_principal,
        cnae_principal_desc=client_in.cnae_principal_desc,
        cnae_secundario=client_in.cnae_secundario,
        cnae_secundario_desc=client_in.cnae_secundario_desc,
        natureza_juridica=client_in.natureza_juridica,
        natureza_juridica_desc=client_in.natureza_juridica_desc,
        logradouro=client_in.logradouro,
        numero=client_in.numero,
        complemento=client_in.complemento,
        cep=client_in.cep,
        bairro=client_in.bairro,
        municipio=client_in.municipio,
        uf=client_in.uf,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    logger.info(f"Cliente criado: {db_client}")
    return db_client

def create_employee(db: Session, employee_in: schemas.EmployeeCreate) -> models.Employee:
    logger.info(f"Criando funcionário para usuário: {employee_in.user.email}")
    db_user = create_user(db, employee_in.user)
    db_employee = models.Employee(
        user_id=db_user.id,
        matricula=employee_in.matricula,
        cpf=employee_in.cpf,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    logger.info(f"Funcionário criado: {db_employee}")
    return db_employee

def get_client_by_user_id(db: Session, user_id: int) -> Optional[models.Client]:
    logger.debug(f"Buscando cliente por user_id: {user_id}")
    client = db.query(models.Client).filter(models.Client.user_id == user_id).first()
    logger.debug(f"Resultado: {client}")
    return client

def get_employee_by_user_id(db: Session, user_id: int) -> Optional[models.Employee]:
    logger.debug(f"Buscando funcionário por user_id: {user_id}")
    employee = db.query(models.Employee).filter(models.Employee.user_id == user_id).first()
    logger.debug(f"Resultado: {employee}")
    return employee

def get_user_by_client_id(db: Session, client_id: int) -> Optional[models.User]:
    logger.debug(f"Buscando usuário por client_id: {client_id}")
    user = db.query(models.User).join(models.Client).filter(models.Client.id == client_id).first()
    logger.debug(f"Resultado: {user}")
    return user

def get_user_by_employee_id(db: Session, employee_id: int) -> Optional[models.User]:
    logger.debug(f"Buscando usuário por employee_id: {employee_id}")
    user = db.query(models.User).join(models.Employee).filter(models.Employee.id == employee_id).first()
    logger.debug(f"Resultado: {user}")
    return user