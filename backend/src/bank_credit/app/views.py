"""The versioned analytics views: SQL lives in bank_credit/sql/views and is shipped as package data."""

from importlib.resources import files

# Dependency order: a view may only read the ones before it.
VIEWS_V1: tuple[str, ...] = (
    "v_request_stage_intervals",
    "v_sla_breach_rate_weekly",
    "v_time_in_stage_weekly",
    "v_throughput_daily",
)


def view_sql(name: str, version: int = 1) -> str:
    """The CREATE VIEW statement of a view, read from the package data."""
    return (files("bank_credit") / "sql" / "views" / f"{name}.v{version}.sql").read_text("utf-8")
