from __future__ import annotations

from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ObservationPeriod
from omop_cohort_builder.base import DateRange, NumericRange, Concept


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_observation_period_basic():
    """Test ObservationPeriod query generation without filters."""
    criteria = ObservationPeriod()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT observation_period.observation_period_id" in sql
    assert "FROM observation_period" in sql


def test_observation_period_dates():
    """Test ObservationPeriod date filters."""
    criteria = ObservationPeriod(
        period_start_date=DateRange(value="2010-01-01", op="gte"),
        period_end_date=DateRange(value="2010-12-31", op="lte"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "observation_period.observation_period_start_date >= '2010-01-01'" in sql
    assert "observation_period.observation_period_end_date <= '2010-12-31'" in sql


def test_observation_period_type():
    """Test ObservationPeriod type filter."""
    c1 = Concept(
        concept_id=1001,
        concept_name="Period Type A",
        domain_id="Type",
        vocabulary_id="Test",
        concept_class_id="Type",
    )
    criteria = ObservationPeriod(period_type=[c1])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "observation_period.period_type_concept_id IN (1001)" in sql


def test_observation_period_length():
    """Test ObservationPeriod length filter."""
    criteria = ObservationPeriod(period_length=NumericRange(value=365, op="gte"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    # Length calculation: end - start
    assert (
        "observation_period.observation_period_end_date - observation_period.observation_period_start_date >= 365"
        in sql
    )
