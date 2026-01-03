from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    CriteriaGroup,
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


@pytest.fixture
def qb():
    return QueryBuilder(concept_set_map={1: [100]})


@pytest.fixture
def primary_events():
    return table(
        "primary_events",
        column("person_id"),
        column("start_date"),
        column("end_date"),
        column("event_id"),
    )


def test_build_criteria_group_all(qb, primary_events):
    """Test CriteriaGroup with Type=ALL."""

    # Group: ALL of (Criteria 1, Criteria 2)
    group = CriteriaGroup(
        type="ALL",
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            ),
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=-30, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            ),
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)

    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Should select from UNION of 2 queries
    assert "UNION ALL" in sql
    # Should group by person_id, event_id
    assert "GROUP BY group_union.person_id, group_union.event_id" in sql
    # ALL means count == total_items (2)
    assert "having count(group_union.index_id) = 2" in sql.lower()


def test_build_criteria_group_any(qb, primary_events):
    """Test CriteriaGroup with Type=ANY."""
    group = CriteriaGroup(
        type="ANY",
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "having count(group_union.index_id) > 0" in sql.lower()


def test_build_criteria_group_at_least(qb, primary_events):
    """Test CriteriaGroup with Type=AT_LEAST 1."""
    group = CriteriaGroup(
        type="AT_LEAST",
        count=1,
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "having count(group_union.index_id) >= 1" in sql.lower()


def test_build_criteria_group_at_most(qb, primary_events):
    """Test CriteriaGroup with Type=AT_MOST 1."""
    group = CriteriaGroup(
        type="AT_MOST",
        count=1,
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # AT_MOST uses LEFT JOIN logic on the UNION result
    assert "left outer join" in sql.lower()
    assert "having count(group_union.index_id) <= 1" in sql.lower()


def test_build_criteria_group_recursive(qb, primary_events):
    """Test nested CriteriaGroups."""
    inner_group = CriteriaGroup(
        type="ANY",
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    # Add a second group to force UNION ALL
    inner_group_2 = CriteriaGroup(type="ANY", count=1)

    outer_group = CriteriaGroup(type="ALL", groups=[inner_group, inner_group_2])

    query = qb.build_criteria_group_query(outer_group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Outer query should have UNION (of nested group result)
    assert "UNION ALL" in sql
    # Outer aggregation (2 items)
    assert "having count(group_union.index_id) = 2" in sql.lower()


def test_build_criteria_group_empty(qb, primary_events):
    """Test empty group."""
    group = CriteriaGroup()
    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Empty group returns 0 index_id for all rows in event_alias (dummy select)
    # But wait, logic: `if group.is_empty(): return select(literal(0), ...)`
    assert "SELECT 0 AS index_id" in sql


def test_build_criteria_group_demographic(qb, primary_events):
    """Test CriteriaGroup with DemographicCriteria."""
    from omop_cohort_builder.domain import DemographicCriteria, NumericRange, DateRange

    group = CriteriaGroup(
        type="ALL",
        demographic_criteria_list=[
            DemographicCriteria(
                age=NumericRange(value=18, op="gt"),
                occurrence_start_date=DateRange(value="2020-01-01", op="gt"),
                occurrence_end_date=DateRange(value="2020-12-31", op="lt"),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Should join person table
    assert "JOIN person" in sql
    # Should apply age filter
    assert (
        "year(primary_events.start_date) - person.year_of_birth > 18" in sql.lower()
        or "extract(year from primary_events.start_date) - person.year_of_birth > 18"
        in sql.lower()
    )
    # Should apply date filters
    assert "primary_events.start_date > '2020-01-01'" in sql
    assert "primary_events.end_date < '2020-12-31'" in sql
    # Should have aggregation
    assert "having count(group_union.index_id) = 1" in sql.lower()


def test_build_criteria_group_demographic_no_dates(qb, primary_events):
    """Test CriteriaGroup with DemographicCriteria without dates."""
    from omop_cohort_builder.domain import DemographicCriteria, NumericRange

    group = CriteriaGroup(
        type="ALL",
        demographic_criteria_list=[
            DemographicCriteria(age=NumericRange(value=18, op="gt"))
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    assert "JOIN person" in sql
    # Should NOT filter by dates (except age calc might use start date)
    assert "primary_events.start_date >" not in sql
    assert "primary_events.end_date <" not in sql


def test_build_criteria_group_at_unknown(qb, primary_events):
    """Test CriteriaGroup with unknown AT_ type."""
    group = CriteriaGroup(
        type="AT_UNKNOWN",  # Starts with AT_ but not AT_LEAST/AT_MOST
        count=1,
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Should not produce HAVING clause for count (skips logic)
    # But it does produce GROUP BY.
    assert "GROUP BY" in sql
    # The inner queries might have HAVING, but the OUTER group aggregation should NOT.
    # The outer group aggregates 'group_union.index_id'.
    assert "having count(group_union.index_id)" not in sql.lower()


def test_build_criteria_group_unknown_root_type(qb, primary_events):
    """Test CriteriaGroup with completely unknown type (not ALL/ANY/AT_*)."""
    group = CriteriaGroup(
        type="UNKNOWN_TYPE",
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                start_window=Window(
                    start=Window.Endpoint(days=0, coeff=-1),
                    end=Window.Endpoint(days=0, coeff=1),
                ),
                occurrence=Occurrence(type=2, count=1),
            )
        ],
    )

    query = qb.build_criteria_group_query(group, primary_events)
    sql = normalize_sql(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
    )

    # Should have GROUP BY but no HAVING clause for the group aggregation
    assert "GROUP BY" in sql
    assert "having count(group_union.index_id)" not in sql.lower()
