# app/database.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega as variáveis de ambiente
load_dotenv()

# URL de conexão do banco de dados
DATABASE_CONNECTION_URI = os.getenv("DATABASE_CONNECTION_URI")

# Cria o engine do SQLAlchemy
engine = create_engine(DATABASE_CONNECTION_URI)

# Cria uma classe SessionLocal que gerencia as sessões do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

# Base declarativa para todos os modelos
Base = declarative_base()


def get_db():
    """
    Dependência do FastAPI para obter uma sessão do banco de dados.
    Use em endpoints com:
        db: Session = Depends(get_db)
    """
    Base.metadata.create_all(bind=engine)
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
