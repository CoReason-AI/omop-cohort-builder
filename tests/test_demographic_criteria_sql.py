from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DemographicCriteria, NumericRange, DateRange
from omop_cohort_builder.base import Concept


def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )


def test_demographic_criteria_age():
    # Age > 18
    criteria = DemographicCriteria(age=NumericRange(value=18, op="gt"))
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    # Check join
    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    # Check filter
    # Note: Age calculation is usually (year(start) - year_of_birth)
    assert (
        "EXTRACT(year FROM observation_period.observation_period_start_date) - person.year_of_birth > 18"
        in sql
    )


def test_demographic_criteria_gender():
    # Gender is Male (Concept 8507)
    criteria = DemographicCriteria(
        gender=[Concept(concept_id=8507, concept_name="MALE")]
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    assert "person.gender_concept_id IN (8507)" in sql


def test_demographic_criteria_race():
    # Race is White (Concept 8527)
    criteria = DemographicCriteria(
        race=[Concept(concept_id=8527, concept_name="WHITE")]
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    assert "person.race_concept_id IN (8527)" in sql


def test_demographic_criteria_ethnicity():
    # Ethnicity is Hispanic (Concept 38003563)
    criteria = DemographicCriteria(
        ethnicity=[Concept(concept_id=38003563, concept_name="HISPANIC")]
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person ON observation_period.person_id = person.person_id" in sql
    assert "person.ethnicity_concept_id IN (38003563)" in sql


def test_demographic_criteria_dates():
    # Occurrence Start Date > 2020-01-01
    criteria = DemographicCriteria(
        occurrence_start_date=DateRange(value="2020-01-01", op="gt"),
        occurrence_end_date=DateRange(value="2020-12-31", op="lt"),
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    # No need to join person if only dates are checked, but the builder might join anyway or stick to observation_period
    # Actually, the spec says DemographicCriteria implies ObservationPeriod events.
    assert "observation_period.observation_period_start_date > '2020-01-01'" in sql
    assert "observation_period.observation_period_end_date < '2020-12-31'" in sql


def test_demographic_criteria_combined():
    criteria = DemographicCriteria(
        age=NumericRange(value=50, op="gte"),
        gender=[Concept(concept_id=8532, concept_name="FEMALE")],
        occurrence_start_date=DateRange(value="2010-01-01", op="gte"),
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = str(compile_query(query)).replace("\n", "").replace("  ", " ")

    assert "JOIN person" in sql
    assert (
        "EXTRACT(year FROM observation_period.observation_period_start_date) - person.year_of_birth >= 50"
        in sql
    )
    assert "person.gender_concept_id IN (8532)" in sql
    assert "observation_period.observation_period_start_date >= '2010-01-01'" in sql
