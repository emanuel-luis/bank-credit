# app/auth.py

from datetime import datetime, timedelta
from typing import Optional
import os
import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import EmailStr

from bank_credit.app import crud, models, schemas
from bank_credit.app.database import get_db
from bank_credit.app.email import send_welcome_email
from bank_credit.app.password_utils import get_password_hash, verify_password

# --- Configuration ---
load_dotenv()

# Load configuration from environment variables with secure defaults
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter()


# --- JWT token creation ---


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Authentication dependencies ---


async def authenticate_user(db: Session, email: str, password: str) -> Optional[models.Client]:
    user = crud.get_client_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Client:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_client_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: models.Client = Depends(get_current_user),
) -> models.Client:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user


# --- Auth endpoints ---


@router.post("/token", response_model=schemas.Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=schemas.Client, tags=["auth"])
async def register_user(user: schemas.ClientCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if CNPJ already exists
    if db.query(models.Client).filter(models.Client.cnpj == user.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    # Check if email already exists
    db_user = crud.get_client_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.Client(
        cnpj=str(user.cnpj),
        full_name=str(user.full_name),
        birth_date=datetime.date.fromisoformat(str(user.birth_date)),
        phone=str(user.phone),
        email=str(user.email),
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    background_tasks.add_task(send_welcome_email, str(db_user.email), str(db_user.full_name))
    return db_user


@router.get("/me", response_model=schemas.Client)
async def read_users_me(current_user: models.Client = Depends(get_current_active_user)):
    return current_user
