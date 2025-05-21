# app/auth.py

from datetime import datetime, UTC, timedelta
from typing import Optional
import logging
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from passlib.context import CryptContext  # ADICIONADO

from bank_credit.app import models, schemas
from bank_credit.app.database import get_db
from bank_credit.app.email import send_welcome_email
from bank_credit.app.views import auth as auth_view

# --- Configuration ---
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
router = APIRouter()
logger = logging.getLogger("bank_credit.routers.auth")

# --- JWT token creation ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    logger.debug(f"[create_access_token] Criando token para: {data}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        logger.debug(f"[create_access_token] Expiração customizada: {expire}")
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.debug(f"[create_access_token] Expiração padrão: {expire}")
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"[create_access_token] Token criado.")
    return encoded_jwt

# --- Authentication dependencies ---

async def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    logger.info(f"[authenticate_user] Autenticando usuário {email}")
    user = auth_view.get_user_by_email(db, email)
    if not user:
        logger.debug(f"[authenticate_user] Usuário {email} não encontrado.")
        return False
    if not auth_view.verify_password(password, user.hashed_password) or not user.is_active:
        logger.debug(f"[authenticate_user] Senha incorreta ou usuário inativo para {email}.")
        return False
    logger.debug(f"[authenticate_user] Usuário {email} autenticado com sucesso.")
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    logger.info(f"[get_current_user] Validando token JWT.")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        logger.debug(f"[get_current_user] Payload extraído: {payload}")
        if email is None:
            logger.warning(f"[get_current_user] Email não encontrado no token.")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"[get_current_user] Erro ao decodificar JWT: {e}")
        raise credentials_exception
    user = auth_view.get_user_by_email(db, email=email)
    if user is None:
        logger.warning(f"[get_current_user] Usuário {email} não encontrado.")
        raise credentials_exception
    logger.debug(f"[get_current_user] Usuário {email} validado.")
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    logger.info(f"[get_current_active_user] Verificando se usuário {getattr(current_user, 'id', None)} está ativo.")
    if not current_user.is_active:
        logger.warning(f"[get_current_active_user] Usuário {getattr(current_user, 'id', None)} inativo.")
        raise HTTPException(status_code=400, detail="Usuário inativo")
    logger.debug(f"[get_current_active_user] Usuário ativo.")
    return current_user

# --- Auth endpoints ---

@router.post("/token", response_model=schemas.Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"[POST /auth/token] Login attempt for {form_data.username}")
    logger.debug(f"[POST /auth/token] Login form data: {form_data}")
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"[POST /auth/token] Login failed for {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"[POST /auth/token] Login successful for {form_data.username}")
        logger.debug(f"[POST /auth/token] User object: {user}")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        logger.debug(f"[POST /auth/token] Token generated for {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"[POST /auth/token] Error during login: {e}")
        raise

@router.post("/register/client", response_model=schemas.Client, tags=["auth"])
async def register_client(
    client: schemas.ClientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    logger.info(f"[POST /auth/register/client] Register client {client.user.email}")
    logger.debug(f"[POST /auth/register/client] Client registration data: {client}")
    try:
        if db.query(models.Client).filter(models.Client.cnpj == client.cnpj).first():
            logger.warning(f"[POST /auth/register/client] CNPJ {client.cnpj} already registered")
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
        if db.query(models.User).filter(models.User.email == client.user.email).first():
            logger.warning(f"[POST /auth/register/client] Email {client.user.email} already registered")
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        # HASH DA SENHA ANTES DE CRIAR O USUÁRIO
        client.user.password = get_password_hash(client.user.password)
        db_client = auth_view.create_client(db, client)
        background_tasks.add_task(send_welcome_email, str(db_client.user.email), str(db_client.user.full_name))
        logger.info(f"[POST /auth/register/client] Client {client.user.email} registered successfully")
        logger.debug(f"[POST /auth/register/client] Client object: {db_client}")
        return db_client
    except Exception as e:
        logger.error(f"[POST /auth/register/client] Error registering client: {e}")
        raise

@router.post("/register/employee", response_model=schemas.Employee, tags=["auth"])
async def register_employee(
    employee: schemas.EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    logger.info(f"[POST /auth/register/employee] Register employee {employee.user.email}")
    logger.debug(f"[POST /auth/register/employee] Employee registration data: {employee}")
    try:
        if db.query(models.Employee).filter(models.Employee.matricula == employee.matricula).first():
            logger.warning(f"[POST /auth/register/employee] Matrícula {employee.matricula} already registered")
            raise HTTPException(status_code=400, detail="Matrícula já cadastrada")
        if db.query(models.Employee).filter(models.Employee.cpf == employee.cpf).first():
            logger.warning(f"[POST /auth/register/employee] CPF {employee.cpf} already registered")
            raise HTTPException(status_code=400, detail="CPF já cadastrado")
        if db.query(models.User).filter(models.User.email == employee.user.email).first():
            logger.warning(f"[POST /auth/register/employee] Email {employee.user.email} already registered")
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        # HASH DA SENHA ANTES DE CRIAR O USUÁRIO
        employee.user.password = get_password_hash(employee.user.password)
        db_employee = auth_view.create_employee(db, employee)
        background_tasks.add_task(send_welcome_email, str(db_employee.user.email), str(db_employee.user.full_name))
        logger.info(f"[POST /auth/register/employee] Employee {employee.user.email} registered successfully")
        logger.debug(f"[POST /auth/register/employee] Employee object: {db_employee}")
        return db_employee
    except Exception as e:
        logger.error(f"[POST /auth/register/employee] Error registering employee: {e}")
        raise

@router.get("/me", response_model=schemas.User, tags=["auth"])
async def read_users_me(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    logger.info(f"[GET /auth/me] User {current_user.id}")
    logger.debug(f"[GET /auth/me] Getting user info for user_id={current_user.id}")
    return current_user