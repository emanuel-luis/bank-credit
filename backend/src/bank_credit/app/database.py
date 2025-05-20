# app/database.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega as variáveis de ambiente
load_dotenv()

# URL de conexão do banco de dados
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Cria o engine do SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cria uma classe SessionLocal que gerencia as sessões do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

# Base declarativa para todos os modelos
Base = declarative_base()
# Base.metadata.create_all(bind=engine)


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
