from __future__ import annotations

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DrugExposure
from omop_cohort_builder.base import NumericRange, Concept
from sqlalchemy.dialects import postgresql


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_drug_exposure_with_age():
    """Test DrugExposure query generation with Age filter."""
    criteria = DrugExposure(age=NumericRange(value=18, op="gt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Must join person table
    assert "JOIN person ON drug_exposure.person_id = person.person_id" in sql
    # Check simplified age calculation: extract(year from start_date) - year_of_birth
    # Normalize whitespace to avoid issues with formatting
    normalized_sql = " ".join(sql.split())
    assert (
        "EXTRACT(year FROM drug_exposure.drug_exposure_start_date) - person.year_of_birth > 18"
        in normalized_sql
    )


def test_drug_exposure_with_gender():
    """Test DrugExposure query generation with Gender filter."""
    c1 = Concept(
        CONCEPT_ID=8507,
        CONCEPT_NAME="Male",
        DOMAIN_ID="Gender",
        VOCABULARY_ID="Gender",
        CONCEPT_CLASS_ID="Gender",
    )
    criteria = DrugExposure(gender=[c1])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "JOIN person ON drug_exposure.person_id = person.person_id" in sql
    assert "person.gender_concept_id IN (8507)" in sql


def test_drug_exposure_with_age_and_gender():
    """Test DrugExposure with both Age and Gender filters."""
    c1 = Concept(
        CONCEPT_ID=8532,
        CONCEPT_NAME="Female",
        DOMAIN_ID="Gender",
        VOCABULARY_ID="Gender",
        CONCEPT_CLASS_ID="Gender",
    )
    criteria = DrugExposure(age=NumericRange(value=65, op="gte"), gender=[c1])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    normalized_sql = " ".join(sql.split())

    assert "JOIN person ON drug_exposure.person_id = person.person_id" in sql
    assert (
        "EXTRACT(year FROM drug_exposure.drug_exposure_start_date) - person.year_of_birth >= 65"
        in normalized_sql
    )
    assert "person.gender_concept_id IN (8532)" in sql
