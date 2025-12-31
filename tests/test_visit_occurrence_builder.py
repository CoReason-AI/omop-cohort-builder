from sqlalchemy import Select
from sqlalchemy.dialects import postgresql
import pytest
from pydantic import ValidationError

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import VisitOccurrence
from omop_cohort_builder.base import Concept, NumericRange, DateRange


def compile_query(query: Select) -> str:
    """Compiles a SQLAlchemy query to a string with literal binds."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_visit_occurrence_basic():
    """Test VisitOccurrence query generation without filters."""
    criteria = VisitOccurrence()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT visit_occurrence.visit_occurrence_id" in sql
    assert "FROM visit_occurrence" in sql


def test_visit_occurrence_visit_type():
    """Test VisitOccurrence query generation with visit_type filter."""
    concept = Concept(
        CONCEPT_ID=9201,
        CONCEPT_NAME="Inpatient Visit",
        DOMAIN_ID="Visit",
        VOCABULARY_ID="Visit",
        CONCEPT_CLASS_ID="Visit",
    )
    criteria = VisitOccurrence(visit_type=[concept])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE visit_occurrence.visit_type_concept_id IN (9201)" in sql


def test_visit_occurrence_source_concept():
    """Test VisitOccurrence with visit_source_concept filter."""
    criteria = VisitOccurrence(visit_source_concept=44818518)
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE visit_occurrence.visit_source_concept_id = 44818518" in sql


def test_visit_occurrence_dates():
    """Test VisitOccurrence with start and end date filters."""
    # Start Date > 2020-01-01
    start_date_range = DateRange(value="2020-01-01", op="gt")
    # End Date < 2021-01-01
    end_date_range = DateRange(value="2021-01-01", op="lt")

    criteria = VisitOccurrence(
        occurrence_start_date=start_date_range, occurrence_end_date=end_date_range
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "visit_occurrence.visit_start_date > '2020-01-01'" in sql
    assert "visit_occurrence.visit_end_date < '2021-01-01'" in sql


def test_visit_occurrence_length():
    """Test VisitOccurrence with visit_length filter."""
    # Length >= 3 days
    length_range = NumericRange(value=3, op="gte")
    criteria = VisitOccurrence(visit_length=length_range)

    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Check for the subtraction expression
    # Note: SQLAlchemy might format this as "visit_occurrence.visit_end_date - visit_occurrence.visit_start_date"
    assert (
        "visit_occurrence.visit_end_date - visit_occurrence.visit_start_date >= 3"
        in sql
    )


def test_visit_occurrence_multiple_filters():
    """Test VisitOccurrence with mixed filters."""
    concept = Concept(
        CONCEPT_ID=9201,
        CONCEPT_NAME="Inpatient Visit",
        DOMAIN_ID="Visit",
        VOCABULARY_ID="Visit",
        CONCEPT_CLASS_ID="Visit",
    )
    criteria = VisitOccurrence(
        visit_type=[concept], visit_length=NumericRange(value=1, op="gt")
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "visit_occurrence.visit_type_concept_id IN (9201)" in sql
    assert (
        "visit_occurrence.visit_end_date - visit_occurrence.visit_start_date > 1" in sql
    )


def test_visit_occurrence_date_ops():
    """Test all date filter operations to ensure coverage."""
    # gt and lt tested in test_visit_occurrence_dates

    # eq
    criteria_eq = VisitOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="eq")
    )
    sql_eq = compile_query(QueryBuilder().build_criteria(criteria_eq))
    assert "visit_occurrence.visit_start_date = '2020-01-01'" in sql_eq

    # gte
    criteria_gte = VisitOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="gte")
    )
    sql_gte = compile_query(QueryBuilder().build_criteria(criteria_gte))
    assert "visit_occurrence.visit_start_date >= '2020-01-01'" in sql_gte

    # lte
    criteria_lte = VisitOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="lte")
    )
    sql_lte = compile_query(QueryBuilder().build_criteria(criteria_lte))
    assert "visit_occurrence.visit_start_date <= '2020-01-01'" in sql_lte

    # bt
    criteria_bt = VisitOccurrence(
        occurrence_start_date=DateRange(
            value="2020-01-01", op="bt", extent="2020-12-31"
        )
    )
    sql_bt = compile_query(QueryBuilder().build_criteria(criteria_bt))
    assert (
        "visit_occurrence.visit_start_date BETWEEN '2020-01-01' AND '2020-12-31'"
        in sql_bt
    )

    # !bt
    criteria_nbt = VisitOccurrence(
        occurrence_start_date=DateRange(
            value="2020-01-01", op="!bt", extent="2020-12-31"
        )
    )
    sql_nbt = compile_query(QueryBuilder().build_criteria(criteria_nbt))
    assert (
        "visit_occurrence.visit_start_date NOT BETWEEN '2020-01-01' AND '2020-12-31'"
        in sql_nbt
    )

    # bt with missing extent
    criteria_bt_none = VisitOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="bt", extent=None)
    )
    sql_bt_none = compile_query(QueryBuilder().build_criteria(criteria_bt_none))
    # Should not apply filter
    assert "BETWEEN" not in sql_bt_none

    # !bt with missing extent
    criteria_nbt_none = VisitOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="!bt", extent=None)
    )
    sql_nbt_none = compile_query(QueryBuilder().build_criteria(criteria_nbt_none))
    # Should not apply filter
    assert "BETWEEN" not in sql_nbt_none

    # Unknown op (fall through) - now raises ValidationError
    with pytest.raises(ValidationError):
        VisitOccurrence(
            occurrence_start_date=DateRange(value="2020-01-01", op="unknown")
        )
