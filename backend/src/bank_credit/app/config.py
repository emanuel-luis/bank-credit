"""Application settings, read from the environment and an optional .env file."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """What Alembic and the CLI jobs need, so they run without SECRET_KEY."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    log_level: str = "INFO"
    # Password of the users created by `bank-credit seed`. Local demo only.
    demo_password: str = "demo1234"


class Settings(DatabaseSettings):
    secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:5173"]

    # When disabled, emails are logged instead of sent.
    mail_enabled: bool = False
    mail_server: str = ""
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = ""
    mail_from_name: str = "Sistema de Crédito Bancário"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()  # type: ignore[call-arg]  # required fields come from the environment
