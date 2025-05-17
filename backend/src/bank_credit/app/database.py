# app/database.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega as variáveis de ambiente
load_dotenv()

# URL de conexão do banco de dados
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank_credit.db")

# Cria o engine do SQLAlchemy
# connect_args é necessário apenas para SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# Cria uma classe SessionLocal que gerencia as sessões do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para todos os modelos
Base = declarative_base()


def get_db():
    """
    Dependência do FastAPI para obter uma sessão do banco de dados.
    Use em endpoints com:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados, criando todas as tabelas.
    """
    Base.metadata.create_all(bind=engine)
