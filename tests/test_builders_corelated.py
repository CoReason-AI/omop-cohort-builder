from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.builders import _get_criteria_columns_dispatch
from omop_cohort_builder.domain import (
    CorelatedCriteria,
    ConditionOccurrence,
    Window,
    Occurrence,
)
from sqlalchemy import table, column
from sqlalchemy.dialects import postgresql
import pytest


def normalize_sql(sql):
    return " ".join(sql.split())


def test_build_corelated_criteria_query_basic():
    """
    Test generating a correlated query for:
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
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    query = qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # Assertions
    # Should join criteria_events (ConditionOccurrence) with primary_events
    # Note: criteria_events is a subquery alias
    assert "JOIN (SELECT condition_occurrence" in normalized
    assert (
        "AS criteria_events ON criteria_events.person_id = primary_events.person_id"
        in normalized
    )

    # Window Logic
    assert (
        "criteria_events.condition_start_date BETWEEN primary_events.start_date + 0 AND primary_events.start_date + 30"
        in normalized
    )
    # Codeset check
    assert "condition_occurrence.condition_concept_id IN (100)" in normalized

    # Aggregation
    assert "GROUP BY primary_events.person_id, primary_events.event_id" in normalized
    assert "HAVING count(*) >= 1" in normalized


def test_build_corelated_criteria_count_check():
    """
    Test "At least 2" which should force a COUNT(*) check >= 2.
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
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    query = qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)

    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Check for count
    assert "count(*) >= 2" in sql.lower()


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
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    query = qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)

    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "count(*) = 5" in sql.lower()


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
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    query = qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)

    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Should use LEFT OUTER JOIN for AT_MOST
    assert "LEFT OUTER JOIN" in sql
    assert "count(*) <= 3" in sql.lower()


def test_build_corelated_criteria_exactly_zero():
    """Test Exactly 0 occurrences (should use LEFT JOIN logic)."""
    window = Window(
        start=Window.Endpoint(days=0, coeff=1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=False,
        use_event_end=False,
    )
    criteria = CorelatedCriteria(
        criteria=ConditionOccurrence(codeset_id=1),
        start_window=window,
        occurrence=Occurrence(type=Occurrence.EXACTLY, count=0),
    )
    qb = QueryBuilder()
    primary_events = table(
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    query = qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)

    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # EXACTLY 0 uses LEFT OUTER JOIN logic
    assert "LEFT OUTER JOIN" in sql
    assert "count(*) = 0" in sql.lower()


def test_build_corelated_criteria_unknown_type():
    """Test unknown occurrence type raises KeyError."""
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
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )

    with pytest.raises(KeyError):
        qb.build_corelated_criteria_query(criteria, primary_events, index_id=0)


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
