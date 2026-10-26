"""Analytics endpoints: auth, scope and parameters. The views exist only on Postgres, so the
query layer is replaced by a fake here; real results are checked in tests/integration."""

from datetime import date

import pytest

from bank_credit.app.domain.enums import UserRole
from bank_credit.app.routers.analytics import Dataset, get_reader

BREACH_ROW = {
    "sector_code": "retail_center",
    "week_start": date(2026, 1, 5),
    "closed": 8,
    "breached": 2,
    "breach_rate": "0.2500",
}
URLS = ["/analytics/sla-breach-rate", "/analytics/time-in-stage", "/analytics/throughput"]


@pytest.fixture
def calls(test_app):
    """Install a fake reader; each call is recorded as (view, from, to, sector)."""
    recorded: list[tuple[str, date, date, str | None]] = []

    def fake_reader():
        def read(dataset: Dataset, start: date, end: date, sector: str | None):
            recorded.append((dataset.view, start, end, sector))
            return [BREACH_ROW] if dataset.view == "v_sla_breach_rate_weekly" else []

        return read

    test_app.app.dependency_overrides[get_reader] = fake_reader
    return recorded


@pytest.mark.parametrize("url", URLS)
def test_customer_and_staff_get_403_forbidden(test_app, calls, auth, customer, retail_staff, url):
    for user in (customer, retail_staff):
        response = test_app.get(url, headers=auth(user))
        assert response.status_code == 403
        assert response.json()["code"] == "forbidden"
    assert calls == []


@pytest.mark.parametrize("url", URLS)
def test_anonymous_gets_401(test_app, calls, url):
    assert test_app.get(url).status_code == 401


def test_manager_is_forced_to_their_sector(test_app, calls, auth, make_employee):
    manager = make_employee(UserRole.MANAGER, "retail_center")
    response = test_app.get("/analytics/sla-breach-rate", headers=auth(manager))
    assert response.status_code == 200
    assert calls[-1][3] == "retail_center"

    own = test_app.get("/analytics/sla-breach-rate?sector=retail_center", headers=auth(manager))
    assert own.status_code == 200


@pytest.mark.parametrize("url", URLS)
def test_manager_asking_another_sector_gets_403(test_app, calls, auth, make_employee, url):
    manager = make_employee(UserRole.MANAGER, "retail_center")
    response = test_app.get(f"{url}?sector=mid_large_center", headers=auth(manager))
    assert response.status_code == 403
    assert response.json()["code"] == "scope_not_allowed"
    assert calls == []


def test_manager_without_a_sector_gets_403(test_app, calls, auth, make_employee):
    manager = make_employee(UserRole.MANAGER, None)
    response = test_app.get("/analytics/throughput", headers=auth(manager))
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_admin_sees_every_sector_or_picks_one(test_app, calls, auth, admin):
    assert test_app.get("/analytics/throughput", headers=auth(admin)).status_code == 200
    assert calls[-1][3] is None
    test_app.get("/analytics/throughput?sector=mid_large_center", headers=auth(admin))
    assert calls[-1][3] == "mid_large_center"


def test_response_shape_and_decimal_strings(test_app, calls, auth, admin, clock):
    response = test_app.get("/analytics/sla-breach-rate", headers=auth(admin))
    body = response.json()
    assert body["source_view"] == "v_sla_breach_rate_weekly"
    assert body["generated_at"].startswith("2026-01-05T10:00:00")
    assert body["data"] == [
        {
            "sector_code": "retail_center",
            "week_start": "2026-01-05",
            "closed": 8,
            "breached": 2,
            "breach_rate": "0.2500",
        }
    ]


def test_default_windows(test_app, calls, auth, admin):
    # The clock is Monday 2026-01-05. Weekly: 12 weeks back, aligned to a Monday. Daily: 90 days.
    test_app.get("/analytics/sla-breach-rate", headers=auth(admin))
    assert calls[-1] == ("v_sla_breach_rate_weekly", date(2025, 10, 13), date(2026, 1, 5), None)
    test_app.get("/analytics/time-in-stage", headers=auth(admin))
    assert calls[-1][1:3] == (date(2025, 10, 13), date(2026, 1, 5))
    test_app.get("/analytics/throughput", headers=auth(admin))
    assert calls[-1] == ("v_throughput_daily", date(2025, 10, 7), date(2026, 1, 5), None)


def test_explicit_window_and_weekly_alignment(test_app, calls, auth, admin):
    # 2025-12-31 is a Wednesday: the weekly view starts at that week's Monday.
    test_app.get("/analytics/sla-breach-rate?from=2025-12-31&to=2026-01-04", headers=auth(admin))
    assert calls[-1][1:3] == (date(2025, 12, 29), date(2026, 1, 4))
    test_app.get("/analytics/throughput?from=2025-12-31&to=2026-01-04", headers=auth(admin))
    assert calls[-1][1:3] == (date(2025, 12, 31), date(2026, 1, 4))


def test_invalid_ranges_and_dates_are_rejected(test_app, calls, auth, admin):
    reversed_range = test_app.get(
        "/analytics/throughput?from=2026-02-01&to=2026-01-01", headers=auth(admin)
    )
    assert reversed_range.status_code == 422
    assert reversed_range.json()["code"] == "invalid_range"
    bad_date = test_app.get("/analytics/throughput?from=yesterday", headers=auth(admin))
    assert bad_date.status_code == 422
    assert bad_date.json()["code"] == "validation_error"
    assert calls == []
