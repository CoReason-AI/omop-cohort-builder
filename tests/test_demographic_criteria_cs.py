from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DemographicCriteria, ConceptSetSelection


def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )


def test_demographic_criteria_gender_cs():
    # Gender CS (Codeset 1)
    criteria = DemographicCriteria(gender_cs=ConceptSetSelection(codeset_id=1))
    # Map codeset 1 to concepts 8507 (Male), 8532 (Female)
    qb = QueryBuilder(concept_set_map={1: [8507, 8532]})
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    # Expect gender_concept_id IN (8507, 8532)
    assert "person.gender_concept_id IN (8507, 8532)" in sql


def test_demographic_criteria_race_cs():
    # Race CS (Codeset 2)
    criteria = DemographicCriteria(race_cs=ConceptSetSelection(codeset_id=2))
    # Map codeset 2 to concepts 8527 (White), 8516 (Black)
    qb = QueryBuilder(concept_set_map={2: [8527, 8516]})
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    assert "person.race_concept_id IN (8527, 8516)" in sql


def test_demographic_criteria_ethnicity_cs():
    # Ethnicity CS (Codeset 3)
    criteria = DemographicCriteria(ethnicity_cs=ConceptSetSelection(codeset_id=3))
    # Map codeset 3 to concepts 38003563 (Hispanic), 38003564 (Not Hispanic)
    qb = QueryBuilder(concept_set_map={3: [38003563, 38003564]})
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    assert "person.ethnicity_concept_id IN (38003563, 38003564)" in sql


def test_demographic_criteria_cs_exclusion():
    # Gender CS Exclude (Codeset 1)
    criteria = DemographicCriteria(
        gender_cs=ConceptSetSelection(codeset_id=1, is_exclusion=True)
    )
    qb = QueryBuilder(concept_set_map={1: [8507]})
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person" in sql
    assert "person.gender_concept_id NOT IN (8507)" in sql
