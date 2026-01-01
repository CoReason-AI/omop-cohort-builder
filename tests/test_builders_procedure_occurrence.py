from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    ProcedureOccurrence,
    ConceptSetSelection,
    Concept,
    NumericRange,
)
from sqlalchemy.dialects import postgresql
import re

def normalize_sql(sql: str) -> str:
    return " ".join(sql.split())

def compile_query(query) -> str:
    return str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

def test_procedure_occurrence_basic():
    qb = QueryBuilder(concept_set_map={100: [1, 2, 3]})
    criteria = ProcedureOccurrence(
        codeset_id=100,
        procedure_source_concept=999,
        quantity=NumericRange(value=5, op="gt")
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "SELECT procedure_occurrence.procedure_occurrence_id" in sql
    assert "FROM procedure_occurrence" in sql
    assert "procedure_occurrence.procedure_concept_id IN (1, 2, 3)" in sql
    assert "procedure_occurrence.procedure_source_concept_id = 999" in sql
    assert "procedure_occurrence.quantity > 5" in sql

def test_procedure_occurrence_procedure_type_cs():
    qb = QueryBuilder(concept_set_map={200: [10, 20]})
    criteria = ProcedureOccurrence(
        procedure_type_cs=ConceptSetSelection(codeset_id=200)
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "procedure_occurrence.procedure_type_concept_id IN (10, 20)" in sql

def test_procedure_occurrence_procedure_type_exclude():
    # Test exclusion with list
    qb = QueryBuilder()
    criteria = ProcedureOccurrence(
        procedure_type=[Concept(CONCEPT_ID=5, CONCEPT_NAME="TypeA")],
        procedure_type_exclude=True
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "procedure_occurrence.procedure_type_concept_id NOT IN (5)" in sql

def test_procedure_occurrence_modifier_cs():
    qb = QueryBuilder(concept_set_map={300: [30, 40]})
    criteria = ProcedureOccurrence(
        modifier_cs=ConceptSetSelection(codeset_id=300)
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "procedure_occurrence.modifier_concept_id IN (30, 40)" in sql

def test_procedure_occurrence_age():
    qb = QueryBuilder()
    criteria = ProcedureOccurrence(
        age=NumericRange(value=50, op="gt")
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "JOIN person ON procedure_occurrence.person_id = person.person_id" in sql
    # Expected SQL for age: EXTRACT(year FROM procedure_occurrence.procedure_date) - person.year_of_birth
    assert "EXTRACT(year FROM procedure_occurrence.procedure_date) - person.year_of_birth > 50" in sql

def test_procedure_occurrence_gender_cs():
    qb = QueryBuilder(concept_set_map={400: [8507, 8532]})
    criteria = ProcedureOccurrence(
        gender_cs=ConceptSetSelection(codeset_id=400)
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "JOIN person ON procedure_occurrence.person_id = person.person_id" in sql
    assert "person.gender_concept_id IN (8507, 8532)" in sql

def test_procedure_occurrence_provider_specialty():
    qb = QueryBuilder(concept_set_map={500: [33, 44]})
    criteria = ProcedureOccurrence(
        provider_specialty_cs=ConceptSetSelection(codeset_id=500)
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "JOIN provider ON procedure_occurrence.provider_id = provider.provider_id" in sql
    assert "provider.specialty_concept_id IN (33, 44)" in sql

def test_procedure_occurrence_visit_type():
    qb = QueryBuilder(concept_set_map={600: [9201]})
    criteria = ProcedureOccurrence(
        visit_type_cs=ConceptSetSelection(codeset_id=600)
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "JOIN visit_occurrence ON procedure_occurrence.visit_occurrence_id = visit_occurrence.visit_occurrence_id" in sql
    assert "visit_occurrence.visit_type_concept_id IN (9201)" in sql

def test_procedure_occurrence_visit_type_list():
    qb = QueryBuilder()
    criteria = ProcedureOccurrence(
        visit_type=[Concept(CONCEPT_ID=88, CONCEPT_NAME="IP")]
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    assert "JOIN visit_occurrence ON procedure_occurrence.visit_occurrence_id = visit_occurrence.visit_occurrence_id" in sql
    assert "visit_occurrence.visit_type_concept_id IN (88)" in sql

def test_procedure_occurrence_multiple_joins():
    # Ensure joins are not duplicated if multiple criteria require them
    qb = QueryBuilder()
    criteria = ProcedureOccurrence(
        age=NumericRange(value=20, op="gt"),
        gender=[Concept(CONCEPT_ID=8507, CONCEPT_NAME="M")],
        provider_specialty=[Concept(CONCEPT_ID=10, CONCEPT_NAME="Spec")]
    )
    query = qb.build_criteria(criteria)
    sql = normalize_sql(compile_query(query))

    # Count occurrences of JOIN
    assert sql.count("JOIN person") == 1
    assert sql.count("JOIN provider") == 1
