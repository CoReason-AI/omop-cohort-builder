import pytest
from sqlalchemy import Select
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ConditionOccurrence, Death
from omop_cohort_builder.base import Concept


def compile_query(query: Select) -> str:
    """Compiles a SQLAlchemy query to a string with literal binds."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_condition_occurrence_basic():
    """Test ConditionOccurrence query generation without filters."""
    criteria = ConditionOccurrence()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT condition_occurrence.condition_occurrence_id" in sql
    assert "FROM condition_occurrence" in sql


def test_condition_occurrence_condition_type():
    """Test ConditionOccurrence query generation with condition_type filter."""
    concept = Concept(
        CONCEPT_ID=123,
        CONCEPT_NAME="Test Concept",
        DOMAIN_ID="Condition",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Clinical Finding",
    )
    criteria = ConditionOccurrence(condition_type=[concept])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE condition_occurrence.condition_type_concept_id IN (123)" in sql


def test_condition_occurrence_condition_type_empty_list():
    """Test ConditionOccurrence query generation with empty condition_type list."""
    criteria = ConditionOccurrence(condition_type=[])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    # Should not have WHERE clause for condition_type
    assert "condition_occurrence.condition_type_concept_id IN" not in sql


def test_condition_occurrence_source_concept():
    """Test ConditionOccurrence query generation with source concept filter."""
    criteria = ConditionOccurrence(condition_source_concept=456)
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE condition_occurrence.condition_source_concept_id = 456" in sql


def test_condition_occurrence_multiple_filters():
    """Test ConditionOccurrence with multiple filters."""
    concept = Concept(
        CONCEPT_ID=123,
        CONCEPT_NAME="Test Concept",
        DOMAIN_ID="Condition",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Clinical Finding",
    )
    criteria = ConditionOccurrence(
        condition_type=[concept], condition_source_concept=456
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "condition_occurrence.condition_type_concept_id IN (123)" in sql
    assert "condition_occurrence.condition_source_concept_id = 456" in sql
    assert "AND" in sql


def test_unimplemented_criteria_raises_error():
    """Test that unimplemented criteria types raise NotImplementedError."""
    # Using Death as a dummy unimplemented criteria
    criteria = Death()
    builder = QueryBuilder()

    with pytest.raises(NotImplementedError) as exc:
        builder.build_criteria(criteria)

    assert "Query builder not implemented for type" in str(exc.value)
