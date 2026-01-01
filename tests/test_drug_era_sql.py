from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DrugEra, DateRange, NumericRange


def test_drug_era_basic_select():
    criteria = DrugEra()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    assert "SELECT drug_era.drug_era_id" in str(sql)
    assert "FROM drug_era" in str(sql)


def test_drug_era_start_date():
    criteria = DrugEra(EraStartDate=DateRange(value="2022-01-01", op="gt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "drug_era.drug_era_start_date > '2022-01-01'" in sql


def test_drug_era_end_date():
    criteria = DrugEra(EraEndDate=DateRange(value="2023-01-01", op="lt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "drug_era.drug_era_end_date < '2023-01-01'" in sql


def test_drug_era_occurrence_count():
    criteria = DrugEra(OccurrenceCount=NumericRange(value=5, op="gte"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    # Note: Column name in schema is drug_exposure_count
    assert "drug_era.drug_exposure_count >= 5" in sql


def test_drug_era_gap_days():
    criteria = DrugEra(GapDays=NumericRange(value=10, op="lt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "drug_era.gap_days < 10" in sql


def test_drug_era_length():
    criteria = DrugEra(EraLength=NumericRange(value=30, op="gt"))
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = " ".join(
        str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        ).split()
    )
    # Length is end - start
    assert "drug_era.drug_era_end_date - drug_era.drug_era_start_date > 30" in sql


# TODO: Add tests for codeset_id, age, gender when implemented
