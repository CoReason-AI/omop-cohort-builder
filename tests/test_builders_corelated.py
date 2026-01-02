from omop_cohort_builder.builders import QueryBuilder

# Import the private dispatch function to test fallback coverage explicitly
from omop_cohort_builder.builders import _get_criteria_columns_dispatch
from omop_cohort_builder.domain import (
    CorelatedCriteria,
    ConditionOccurrence,
    Window,
    Occurrence,
)
from sqlalchemy import table, column, select
from sqlalchemy.dialects import postgresql
import pytest


def normalize_sql(sql):
    return " ".join(sql.split())


def test_build_corelated_criteria_expression_basic():
    """
    Test generating a correlated subquery expression for:
    "At least 1 ConditionOccurrence of Concept X
     starting between 0 days before and 30 days after the primary event start date."
    """
    window = Window(
        start=Window.Endpoint(days=0, coeff=-1),
        end=Window.Endpoint(days=30, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )

    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=2, count=1),  # At Least 1
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )

    expr = qb._build_corelated_criteria_expression(criteria, primary_events)

    query = select(primary_events).where(expr)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # Assertions
    assert "criteria_events.person_id = primary_events.person_id" in normalized
    assert (
        "criteria_events.condition_start_date BETWEEN primary_events.start_date + 0 AND primary_events.start_date + 30"
        in normalized
    )
    assert "condition_occurrence.condition_concept_id IN (100)" in normalized
    assert "EXISTS" in normalized


def test_build_corelated_criteria_count_check():
    """
    Test "At least 2" which should force a COUNT(*) check.
    """
    window = Window(
        start=Window.Endpoint(days=0, coeff=1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )

    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=2, count=2),  # At Least 2
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )

    expr = qb._build_corelated_criteria_expression(criteria, primary_events)
    query = select(primary_events).where(expr)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Check for count
    assert "count(*)" in sql.lower() or "count(" in sql.lower()
    assert ">= 2" in sql


def test_build_corelated_criteria_exactly():
    """Test Exactly N occurrences."""
    window = Window(
        start=Window.Endpoint(days=0, coeff=1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )
    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=Occurrence.EXACTLY, count=5),
    )
    qb = QueryBuilder()
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )
    expr = qb._build_corelated_criteria_expression(criteria, primary_events)
    query = select(primary_events).where(expr)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "count(" in sql.lower()
    assert "= 5" in sql


def test_build_corelated_criteria_at_most():
    """Test At Most N occurrences."""
    window = Window(
        start=Window.Endpoint(days=0, coeff=1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )
    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=Occurrence.AT_MOST, count=3),
    )
    qb = QueryBuilder()
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )
    expr = qb._build_corelated_criteria_expression(criteria, primary_events)
    query = select(primary_events).where(expr)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "count(" in sql.lower()
    assert "<= 3" in sql


def test_build_corelated_criteria_unknown_type():
    """Test unknown occurrence type raises NotImplementedError."""
    window = Window(
        start=Window.Endpoint(days=0, coeff=1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )
    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=999, count=1),
    )
    qb = QueryBuilder()
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )

    with pytest.raises(NotImplementedError):
        qb._build_corelated_criteria_expression(criteria, primary_events)


def test_apply_window_logic_index_end():
    """
    Test window logic relative to Index End Date.
    """
    window = Window(
        start=Window.Endpoint(days=5, coeff=1),
        end=Window.Endpoint(days=10, coeff=1),
        use_index_end=True,  # Use primary_events.end_date
        use_event_end=False,
    )

    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=2, count=1),
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    primary_events = table(
        "primary_events", column("person_id"), column("start_date"), column("end_date")
    )

    expr = qb._build_corelated_criteria_expression(criteria, primary_events)
    query = select(primary_events).where(expr)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # Check usage of primary_events.end_date
    assert (
        "BETWEEN primary_events.end_date + 5 AND primary_events.end_date + 10"
        in normalized
    )


def test_get_criteria_columns_unimplemented_direct():
    """
    Explicitly test _get_criteria_columns_dispatch fallback using direct registry access.
    """

    class DummyCriteria:
        pass

    # Access the default implementation directly from the registry
    default_impl = _get_criteria_columns_dispatch.registry[object]

    with pytest.raises(NotImplementedError):
        default_impl(DummyCriteria())


def test_get_criteria_columns_method_call():
    """Test that the wrapper method call works (and covers the return line)."""
    qb = QueryBuilder()
    c = ConditionOccurrence(codeset_id=1)
    cols = qb._get_criteria_columns(c)
    assert cols is not None
