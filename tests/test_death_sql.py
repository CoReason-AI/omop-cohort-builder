from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import Death
from omop_cohort_builder.base import DateRange, Concept


def test_build_death_minimal():
    criteria = Death()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ).string
    assert "SELECT death.person_id, death.death_date" in sql
    assert "FROM death" in sql


def test_build_death_with_death_type():
    criteria = Death(
        death_type=[
            Concept(CONCEPT_ID=1, CONCEPT_NAME="Type A"),
            Concept(CONCEPT_ID=2, CONCEPT_NAME="Type B"),
        ]
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ).string

    assert "death.death_type_concept_id IN (1, 2)" in sql


def test_build_death_with_source_concept():
    criteria = Death(death_source_concept=12345)
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ).string

    assert "death.cause_source_concept_id = 12345" in sql


def test_build_death_with_date():
    criteria = Death(occurrence_start_date=DateRange(value="2023-01-01", op="gt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ).string

    assert "death.death_date > '2023-01-01'" in sql


def test_build_death_all_fields():
    criteria = Death(
        death_type=[Concept(CONCEPT_ID=1, CONCEPT_NAME="A")],
        death_source_concept=999,
        occurrence_start_date=DateRange(value="2020-01-01", op="eq"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ).string

    assert "death.death_type_concept_id IN (1)" in sql
    assert "death.cause_source_concept_id = 999" in sql
    assert "death.death_date = '2020-01-01'" in sql
