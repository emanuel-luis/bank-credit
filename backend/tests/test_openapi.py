import os
import subprocess
import sys
from pathlib import Path

from bank_credit.app.cli import openapi_json

COMMITTED = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "openapi.json"


def test_committed_openapi_is_current():
    expected = openapi_json().encode()
    assert COMMITTED.read_bytes() == expected, (
        "the API contract changed: run `cd backend && uv run bank-credit openapi "
        "--out ../frontend/src/api/openapi.json` and commit the result"
    )


def test_openapi_command_needs_no_environment():
    env = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "DATABASE_URL")}
    code = "from bank_credit.app.cli import main; main(['openapi'])"
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, check=True, timeout=60
    )
    assert result.stdout == COMMITTED.read_bytes()
