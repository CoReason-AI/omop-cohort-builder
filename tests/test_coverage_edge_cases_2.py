from __future__ import annotations

from sqlalchemy import select, column
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.base import NumericRange, DateRange, RangeType

# Dummy table column for testing
test_col = column("test_col")


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_numeric_filter_bt_missing_extent():
    """Test numeric filter BT with missing extent (coverage gap)."""
    # Create criteria with BT but extent=None
    # We cheat by using construct directly if needed, but Pydantic might allow optional extent
    criteria_range = NumericRange(value=5, op=RangeType.BT, extent=None)

    qb = QueryBuilder()
    query = select(test_col)

    # This should hit the 'if criteria_range.extent is not None:' check and skip the filter
    query = qb._apply_numeric_filter(query, test_col, criteria_range)

    sql = compile_query(query)
    assert "BETWEEN" not in sql
    assert "WHERE" not in sql


def test_numeric_filter_not_bt_missing_extent():
    """Test numeric filter NOT_BT with missing extent (coverage gap)."""
    criteria_range = NumericRange(value=5, op=RangeType.NOT_BT, extent=None)

    qb = QueryBuilder()
    query = select(test_col)

    # This should hit the 'if criteria_range.extent is not None:' check and skip the filter
    query = qb._apply_numeric_filter(query, test_col, criteria_range)

    sql = compile_query(query)
    assert "BETWEEN" not in sql
    assert "WHERE" not in sql


def test_date_filter_bt_missing_extent():
    """Test date filter BT with missing extent (coverage gap)."""
    criteria_range = DateRange(value="2020-01-01", op=RangeType.BT, extent=None)

    qb = QueryBuilder()
    query = select(test_col)

    query = qb._apply_date_filter(query, test_col, criteria_range)

    sql = compile_query(query)
    assert "BETWEEN" not in sql
    assert "WHERE" not in sql


def test_date_filter_not_bt_missing_extent():
    """Test date filter NOT_BT with missing extent (coverage gap)."""
    criteria_range = DateRange(value="2020-01-01", op=RangeType.NOT_BT, extent=None)

    qb = QueryBuilder()
    query = select(test_col)

    query = qb._apply_date_filter(query, test_col, criteria_range)

    sql = compile_query(query)
    assert "BETWEEN" not in sql
    assert "WHERE" not in sql
