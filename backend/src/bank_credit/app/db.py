"""Declarative base, column types, engine and session factories."""

from collections.abc import Iterator
from datetime import UTC, datetime
from enum import Enum
from functools import lru_cache

from sqlalchemy import DateTime, Engine, MetaData, create_engine
from sqlalchemy import Enum as SAEnum
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from bank_credit.app.config import get_database_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class UTCDateTime(TypeDecorator[datetime]):
    """timestamptz that only accepts tz-aware values and always returns UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("naive datetime: pass a timezone-aware value")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        # SQLite returns naive values: they were stored as UTC.
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


Base.registry.update_type_annotation_map({datetime: UTCDateTime})


def enum_column(enum_cls: type[Enum], name: str, length: int) -> SAEnum:
    """VARCHAR + CHECK storing the enum values, not the member names."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_database_settings().database_url)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed afterwards."""
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "UTCDateTime", "enum_column", "get_db", "get_engine", "get_sessionmaker"]
