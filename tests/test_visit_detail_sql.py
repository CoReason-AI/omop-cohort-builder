from sqlalchemy import Select
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import VisitDetail
from omop_cohort_builder.base import NumericRange, DateRange


def compile_query(query: Select) -> str:
    """Compiles a SQLAlchemy query to a string with literal binds."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_visit_detail_basic():
    """Test VisitDetail query generation without filters."""
    criteria = VisitDetail()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT visit_detail.visit_detail_id" in sql
    assert "FROM visit_detail" in sql


def test_visit_detail_source_concept():
    """Test VisitDetail with visit_detail_source_concept filter."""
    criteria = VisitDetail(visit_detail_source_concept=44818518)
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE visit_detail.visit_detail_source_concept_id = 44818518" in sql


def test_visit_detail_dates():
    """Test VisitDetail with start and end date filters."""
    # Start Date > 2020-01-01
    start_date_range = DateRange(value="2020-01-01", op="gt")
    # End Date < 2021-01-01
    end_date_range = DateRange(value="2021-01-01", op="lt")

    criteria = VisitDetail(
        visit_detail_start_date=start_date_range, visit_detail_end_date=end_date_range
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "visit_detail.visit_detail_start_date > '2020-01-01'" in sql
    assert "visit_detail.visit_detail_end_date < '2021-01-01'" in sql


def test_visit_detail_length():
    """Test VisitDetail with visit_detail_length filter."""
    # Length >= 3 days
    length_range = NumericRange(value=3, op="gte")
    criteria = VisitDetail(visit_detail_length=length_range)

    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Check for the subtraction expression
    assert (
        "visit_detail.visit_detail_end_date - visit_detail.visit_detail_start_date >= 3"
        in sql
    )


def test_visit_detail_multiple_filters():
    """Test VisitDetail with mixed filters."""
    criteria = VisitDetail(
        visit_detail_source_concept=12345,
        visit_detail_length=NumericRange(value=1, op="gt"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "visit_detail.visit_detail_source_concept_id = 12345" in sql
    assert (
        "visit_detail.visit_detail_end_date - visit_detail.visit_detail_start_date > 1"
        in sql
    )
