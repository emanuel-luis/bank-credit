from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from bank_credit.app.db import get_db


def test_health_ok(test_app: TestClient) -> None:
    response = test_app.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_unavailable_when_db_is_down(test_app: TestClient) -> None:
    class BrokenSession:
        def execute(self, *_args: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    test_app.app.dependency_overrides[get_db] = lambda: BrokenSession()  # type: ignore[attr-defined]
    response = test_app.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
