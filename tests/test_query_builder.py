from sqlalchemy import Select
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ConditionOccurrence


def compile_query(query: Select) -> str:
    """Helper to compile query to string for assertions"""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_build_condition_occurrence_basic():
    # Arrange
    criteria = ConditionOccurrence(
        codeset_id=1
    )  # Minimal criteria, though codeset_id isn't used yet
    builder = QueryBuilder()

    # Act
    query = builder.build_condition_occurrence(criteria)
    sql = compile_query(query)

    # Assert
    # Basic check: should select from condition_occurrence
    assert "SELECT" in sql
    assert "FROM condition_occurrence" in sql
    # Ensure all columns are selected (default select(*))
    assert "condition_occurrence.condition_occurrence_id" in sql
    assert "condition_occurrence.person_id" in sql
