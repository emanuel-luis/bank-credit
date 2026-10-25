# app/database.py
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from bank_credit.app.config import get_settings

# Base declarativa para todos os modelos
Base = declarative_base()


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=True, bind=get_engine())


def get_db() -> Iterator[Session]:
    """
    Dependência do FastAPI para obter uma sessão do banco de dados.
    Use em endpoints com:
        db: Session = Depends(get_db)
    """
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados, criando todas as tabelas.
    """
    Base.metadata.create_all(bind=get_engine())
