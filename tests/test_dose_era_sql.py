from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DoseEra, DateRange, NumericRange, Concept


def test_dose_era_basic_sql():
    criteria = DoseEra(
        era_start_date=DateRange(value="2022-01-01", op="gt"),
        era_end_date=DateRange(value="2022-12-31", op="lt"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    query_str = str(sql)

    expected_snippets = [
        "SELECT dose_era.dose_era_id",
        "FROM dose_era",
        "dose_era.dose_era_start_date > '2022-01-01'",
        "dose_era.dose_era_end_date < '2022-12-31'",
    ]
    for snippet in expected_snippets:
        assert snippet in query_str


def test_dose_era_dose_value_sql():
    criteria = DoseEra(dose_value=NumericRange(value=50, op="gt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    query_str = str(sql)

    assert "dose_era.dose_value > 50" in query_str


def test_dose_era_unit_sql():
    criteria = DoseEra(
        unit=[
            Concept(
                concept_id=123,
                concept_name="Unit A",
                standard_concept="S",
                concept_code="A",
                domain_id="Unit",
                vocabulary_id="V",
                concept_class_id="C",
            )
        ]
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    query_str = str(sql)

    assert "dose_era.unit_concept_id IN (123)" in query_str


def test_dose_era_length_sql():
    criteria = DoseEra(era_length=NumericRange(value=10, op="gte"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    query_str = str(sql)

    # Normalizing whitespace for the expression check
    query_str_clean = " ".join(query_str.split())
    expected_expr = "dose_era.dose_era_end_date - dose_era.dose_era_start_date >= 10"
    assert expected_expr in query_str_clean
