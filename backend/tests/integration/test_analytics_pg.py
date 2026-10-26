"""The analytics views and endpoints against real Postgres, checked with aggregates computed in
Python from the same request_events."""

import statistics
from collections import Counter, defaultdict
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from bank_credit.app.db import get_db
from bank_credit.app.main import create_app
from bank_credit.app.security import create_access_token

from .helpers import monday, python_intervals, rate

pytestmark = pytest.mark.integration


def rows(engine: Engine, view: str) -> list[dict]:
    with engine.connect() as connection:
        return [dict(r) for r in connection.execute(text(f"SELECT * FROM {view}")).mappings()]


def test_the_history_is_big_enough_to_mean_something(simulated_engine):
    intervals = python_intervals(simulated_engine)
    closed = [i for i in intervals if i.exited_at]
    assert len(closed) > 20
    assert any(i.breached for i in closed) and not all(i.breached for i in closed)
    assert any(i.exited_at is None for i in intervals)  # some requests are still open


def test_stage_intervals_view_matches_python(simulated_engine):
    expected = {(i.request_id, i.entry_seq): i for i in python_intervals(simulated_engine)}
    actual = {
        (r["request_id"], r["entry_seq"]): r
        for r in rows(simulated_engine, "v_request_stage_intervals")
    }
    assert actual.keys() == expected.keys()
    for key, row in actual.items():
        want = expected[key]
        assert (row["stage_code"], row["sector_code"]) == (want.stage, want.sector)
        assert row["entered_at"] == want.entered_at
        assert row["exited_at"] == want.exited_at
        assert row["exit_event"] == want.exit_event
        assert row["sla_due_at"] == want.sla_due_at
        if want.exited_at is None:
            assert row["duration_s"] is None and row["sla_breached"] is None
        else:
            assert float(row["duration_s"]) == pytest.approx(want.seconds, abs=1e-5)
            assert row["sla_breached"] is want.breached


def test_breach_rate_view_matches_python(simulated_engine):
    counts: dict[tuple[str, date], list[int]] = defaultdict(lambda: [0, 0])
    for i in python_intervals(simulated_engine):
        if i.exited_at is None:
            continue
        bucket = counts[(i.sector, monday(i.exited_at.astimezone(UTC).date()))]
        bucket[0] += 1
        bucket[1] += i.breached
    actual = {
        (r["sector_code"], r["week_start"]): r
        for r in rows(simulated_engine, "v_sla_breach_rate_weekly")
    }
    assert actual.keys() == counts.keys()
    for key, (closed, breached) in counts.items():
        assert (actual[key]["closed"], actual[key]["breached"]) == (closed, breached)
        assert actual[key]["breach_rate"] == rate(breached, closed)
        assert Decimal(0) <= actual[key]["breach_rate"] <= Decimal(1)
    assert all(week.weekday() == 0 for _, week in actual)  # Monday buckets


def test_throughput_view_matches_python(simulated_engine):
    expected: dict[tuple[str, date], Counter[str]] = defaultdict(Counter)
    for i in python_intervals(simulated_engine):
        expected[(i.sector, i.entered_at.astimezone(UTC).date())]["entered"] += 1
        if i.exited_at and i.exit_event:
            kind = "approved" if i.exit_event == "STAGE_APPROVED" else i.exit_event.lower()
            expected[(i.sector, i.exited_at.astimezone(UTC).date())][kind] += 1
    actual = {(r["sector_code"], r["day"]): r for r in rows(simulated_engine, "v_throughput_daily")}
    assert actual.keys() == expected.keys()
    columns = ["entered", "approved", "returned", "rejected", "cancelled", "expired"]
    for key, counter in expected.items():
        assert {c: actual[key][c] for c in columns} == {c: counter[c] for c in columns}
    assert {k for c in expected.values() for k in c} <= set(columns)


def test_time_in_stage_view_matches_python(simulated_engine):
    durations: dict[tuple[str, str, date], list[float]] = defaultdict(list)
    for i in python_intervals(simulated_engine):
        if i.exited_at:
            key = (i.stage, i.sector, monday(i.exited_at.astimezone(UTC).date()))
            durations[key].append(i.seconds / 3600)
    actual = {
        (r["stage_code"], r["sector_code"], r["week_start"]): r
        for r in rows(simulated_engine, "v_time_in_stage_weekly")
    }
    assert actual.keys() == durations.keys()
    tolerance = Decimal("0.01")
    for key, hours in durations.items():
        row = actual[key]
        assert row["n"] == len(hours)
        assert abs(row["avg_h"] - Decimal(str(statistics.fmean(hours)))) <= tolerance
        assert row["p50_h"] <= row["p90_h"]
    # The median of the busiest bucket, against Python's statistics.median.
    busiest = max(durations, key=lambda k: len(durations[k]))
    assert len(durations[busiest]) >= 3
    assert (
        abs(actual[busiest]["p50_h"] - Decimal(str(statistics.median(durations[busiest]))))
        <= tolerance
    )


# --- Endpoints ---


@pytest.fixture
def client(simulated_engine) -> Iterator[TestClient]:
    app = create_app(cors_origins=[])

    def session() -> Iterator[Session]:
        with Session(simulated_engine) as db:
            yield db

    app.dependency_overrides[get_db] = session
    with TestClient(app) as test_client:
        yield test_client


def headers(email: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}


PARAMS = {"from": "2025-01-01", "to": "2026-12-31"}


def test_admin_reads_every_endpoint_and_sees_all_sectors(client):
    admin = headers("admin@example.com")
    breach = client.get("/analytics/sla-breach-rate", params=PARAMS, headers=admin)
    assert breach.status_code == 200
    body = breach.json()
    assert body["source_view"] == "v_sla_breach_rate_weekly"
    assert len(body["data"]) > 0
    assert {r["sector_code"] for r in body["data"]} >= {"retail_center", "mid_large_center"}
    assert isinstance(body["data"][0]["breach_rate"], str)  # decimals are JSON strings
    for path in ("time-in-stage", "throughput"):
        assert client.get(f"/analytics/{path}", params=PARAMS, headers=admin).status_code == 200


def test_endpoint_rows_equal_the_view_rows(client, simulated_engine):
    response = client.get(
        "/analytics/throughput", params=PARAMS, headers=headers("admin@example.com")
    )
    from_api = {(r["sector_code"], r["day"]): r["entered"] for r in response.json()["data"]}
    from_view = {
        (r["sector_code"], r["day"].isoformat()): r["entered"]
        for r in rows(simulated_engine, "v_throughput_daily")
    }
    assert from_api == from_view


def test_manager_gets_only_their_sector_and_403_for_another(client):
    manager = headers("manager.retail_center@example.com")
    own = client.get("/analytics/sla-breach-rate", params=PARAMS, headers=manager)
    assert own.status_code == 200
    assert {r["sector_code"] for r in own.json()["data"]} == {"retail_center"}

    other = client.get(
        "/analytics/sla-breach-rate",
        params={**PARAMS, "sector": "mid_large_center"},
        headers=manager,
    )
    assert other.status_code == 403
    assert other.json()["code"] == "scope_not_allowed"


def test_staff_and_customers_get_403(client):
    for email in ("staff1.retail_center@example.com", "customer1@example.com"):
        response = client.get("/analytics/throughput", headers=headers(email))
        assert (response.status_code, response.json()["code"]) == (403, "forbidden")


def test_default_window_returns_recent_weeks_only(client):
    # The history ended on 2026-03-01 and "today" is later, so the default window may be empty;
    # it must still be a valid, well-formed response.
    response = client.get("/analytics/sla-breach-rate", headers=headers("admin@example.com"))
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)
    assert datetime.fromisoformat(response.json()["generated_at"]).tzinfo is not None
