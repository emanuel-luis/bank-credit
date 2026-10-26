"""The versioned view SQL: packaged, readable, and safe to hand to op.execute()."""

import re

import pytest

from bank_credit.app.views import VIEWS_V1, view_sql


@pytest.mark.parametrize("name", VIEWS_V1)
def test_view_file_is_documented_and_creates_the_view(name):
    sql = view_sql(name)
    assert sql.startswith(f"-- {name} (v1)")
    assert "Grain:" in sql and "Meaning:" in sql
    assert f"CREATE VIEW {name} AS" in sql
    assert sql.rstrip().endswith(";")


@pytest.mark.parametrize("name", VIEWS_V1)
def test_view_sql_has_nothing_a_bind_parameter_parser_would_touch(name):
    sql = view_sql(name)
    assert "%" not in sql
    assert not re.search(r"(?<![:\w]):\w", sql)  # a ":name" would be read as a bind parameter


def test_views_are_listed_in_dependency_order():
    created: set[str] = set()
    for name in VIEWS_V1:
        used = {other for other in VIEWS_V1 if other != name and other in view_sql(name)}
        assert used <= created, f"{name} reads a view created after it"
        created.add(name)
