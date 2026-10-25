"""Password hashing and JWT helpers."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from bank_credit.app.config import get_settings

_password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "iat": now, "exp": expire}
    return jwt.encode(
        payload, settings.secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> str | None:
    """Return the token subject, or None when the token is invalid, expired or has no subject."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    return payload.get("sub")
