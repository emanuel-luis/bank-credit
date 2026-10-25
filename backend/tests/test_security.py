from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import status
from pydantic import ValidationError

from bank_credit.app.config import get_settings


def test_settings_require_secret_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no .env to fall back on
    monkeypatch.delenv("SECRET_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="secret_key"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_token_signed_with_other_key_is_rejected(test_app, client):
    now = datetime.now(UTC)
    forged = jwt.encode(
        {"sub": client.user.email, "iat": now, "exp": now + timedelta(minutes=5)},
        "another-fake-key-" + "y" * 47,
        algorithm="HS256",
    )
    response = test_app.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
