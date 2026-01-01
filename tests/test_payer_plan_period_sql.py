from __future__ import annotations

from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import PayerPlanPeriod
from omop_cohort_builder.base import DateRange, NumericRange


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_payer_plan_period_basic():
    """Test PayerPlanPeriod query generation without filters."""
    criteria = PayerPlanPeriod()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT payer_plan_period.payer_plan_period_id" in sql
    assert "FROM payer_plan_period" in sql


def test_payer_plan_period_dates():
    """Test PayerPlanPeriod date filters."""
    criteria = PayerPlanPeriod(
        period_start_date=DateRange(value="2010-01-01", op="gte"),
        period_end_date=DateRange(value="2010-12-31", op="lte"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "payer_plan_period.payer_plan_period_start_date >= '2010-01-01'" in sql
    assert "payer_plan_period.payer_plan_period_end_date <= '2010-12-31'" in sql


def test_payer_plan_period_length():
    """Test PayerPlanPeriod length filter."""
    criteria = PayerPlanPeriod(period_length=NumericRange(value=365, op="gte"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    # Length calculation: end - start
    assert (
        "payer_plan_period.payer_plan_period_end_date - payer_plan_period.payer_plan_period_start_date >= 365"
        in sql
    )


def test_payer_plan_period_source_concepts():
    """Test PayerPlanPeriod source concept filters."""
    criteria = PayerPlanPeriod(
        payer_source_concept=101,
        plan_source_concept=102,
        sponsor_source_concept=103,
        stop_reason_source_concept=104,
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "payer_plan_period.payer_source_concept_id = 101" in sql
    assert "payer_plan_period.plan_source_concept_id = 102" in sql
    assert "payer_plan_period.sponsor_source_concept_id = 103" in sql
    assert "payer_plan_period.stop_reason_source_concept_id = 104" in sql
