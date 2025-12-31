from __future__ import annotations

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import Observation
from omop_cohort_builder.base import Concept, TextFilter, NumericRange, DateRange
from sqlalchemy.dialects import postgresql


def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )


def test_build_observation_simple():
    qb = QueryBuilder()
    criteria = Observation()

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "SELECT observation.observation_id" in sql
    assert "FROM observation" in sql


def test_build_observation_with_concepts():
    qb = QueryBuilder()
    criteria = Observation(
        observation_type=[Concept(concept_id=123, concept_name="Type")],
        value_as_concept=[Concept(concept_id=456, concept_name="Value")],
        qualifier=[Concept(concept_id=789, concept_name="Qualifier")],
        unit=[Concept(concept_id=101, concept_name="Unit")],
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "observation.observation_type_concept_id IN (123)" in sql
    assert "observation.value_as_concept_id IN (456)" in sql
    assert "observation.qualifier_concept_id IN (789)" in sql
    assert "observation.unit_concept_id IN (101)" in sql


def test_build_observation_numeric_filter():
    qb = QueryBuilder()
    criteria = Observation(
        value_as_number=NumericRange(value=10.5, op="gt"),
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "observation.value_as_number > 10.5" in sql


def test_build_observation_text_filter():
    qb = QueryBuilder()
    criteria = Observation(
        value_as_string=TextFilter(text="test", op="contains"),
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    # Expect escaped wildcards for SQLAlchemy like '%test%'
    # Note: SQLAlchemy dialect=postgresql literal_binds=True might escape % as %%
    assert "observation.value_as_string LIKE '%%test%%'" in sql


def test_build_observation_source_concept():
    qb = QueryBuilder()
    criteria = Observation(observation_source_concept=999)

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "observation.observation_source_concept_id = 999" in sql


def test_build_observation_date_filter():
    qb = QueryBuilder()
    criteria = Observation(occurrence_start_date=DateRange(value="2023-01-01", op="gt"))

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "observation.observation_date > '2023-01-01'" in sql
