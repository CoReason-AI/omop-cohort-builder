from __future__ import annotations

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ConditionOccurrence
from omop_cohort_builder.base import TextFilter, Concept
from sqlalchemy.dialects import postgresql


def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )


def normalize(s):
    return " ".join(s.split())


def test_build_condition_occurrence_stop_reason():
    qb = QueryBuilder()
    criteria = ConditionOccurrence(stop_reason=TextFilter(text="resolved", op="eq"))

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "condition_occurrence.stop_reason = 'resolved'" in sql


def test_build_condition_occurrence_condition_status():
    qb = QueryBuilder()
    criteria = ConditionOccurrence(
        condition_status=[Concept(concept_id=123, concept_name="Provisional")]
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "condition_occurrence.condition_status_concept_id IN (123)" in sql
