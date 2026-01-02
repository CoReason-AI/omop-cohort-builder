from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    ConditionEra,
    NumericRange,
    Concept,
    ConceptSetSelection,
)


def test_condition_era_age_at_start():
    criteria = ConditionEra(age_at_start=NumericRange(value=18, op="gt"))
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    # Verify join to person table
    assert "JOIN person ON condition_era.person_id = person.person_id" in sql_str
    # Verify calculation
    assert (
        "EXTRACT(year FROM condition_era.condition_era_start_date) - person.year_of_birth > 18"
        in sql_str
    )


def test_condition_era_age_at_end():
    criteria = ConditionEra(age_at_end=NumericRange(value=65, op="lt"))
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "JOIN person ON condition_era.person_id = person.person_id" in sql_str
    assert (
        "EXTRACT(year FROM condition_era.condition_era_end_date) - person.year_of_birth < 65"
        in sql_str
    )


def test_condition_era_gender_list():
    criteria = ConditionEra(
        gender=[
            Concept(concept_id=8507, concept_name="Male"),
            Concept(concept_id=8532, concept_name="Female"),
        ]
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "JOIN person ON condition_era.person_id = person.person_id" in sql_str
    assert "person.gender_concept_id IN (8507, 8532)" in sql_str


def test_condition_era_gender_cs_inclusion():
    criteria = ConditionEra(gender_cs=ConceptSetSelection(codeset_id=1))
    concept_map = {1: [8507, 8532]}
    qb = QueryBuilder(concept_set_map=concept_map)
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "JOIN person ON condition_era.person_id = person.person_id" in sql_str
    assert "person.gender_concept_id IN (8507, 8532)" in sql_str


def test_condition_era_gender_cs_exclusion():
    criteria = ConditionEra(
        gender_cs=ConceptSetSelection(codeset_id=1, is_exclusion=True)
    )
    concept_map = {1: [8507]}
    qb = QueryBuilder(concept_set_map=concept_map)
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "JOIN person ON condition_era.person_id = person.person_id" in sql_str
    assert "person.gender_concept_id NOT IN (8507)" in sql_str


def test_condition_era_combined_demographics():
    criteria = ConditionEra(
        age_at_start=NumericRange(value=20, op="gte"),
        gender=[Concept(concept_id=8507)],
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    # Should only join once
    assert sql_str.count("JOIN person") == 1
    assert "person.gender_concept_id IN (8507)" in sql_str
    assert (
        "EXTRACT(year FROM condition_era.condition_era_start_date) - person.year_of_birth >= 20"
        in sql_str
    )
