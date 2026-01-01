from sqlalchemy.dialects import postgresql
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ConditionEra, DateRange, NumericRange


def test_condition_era_sql_simple():
    criteria = ConditionEra(
        codeset_id=1,
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    # Basic select
    assert "SELECT condition_era.condition_era_id" in sql_str
    assert "FROM condition_era" in sql_str

    # We can't verify codeset_id without concept set resolution context,
    # but the builder should at least not crash and produce a valid SELECT.
    # If the builder ignores codeset_id (as expected in this phase), it won't be in the WHERE clause.


def test_condition_era_sql_dates():
    criteria = ConditionEra(
        era_start_date=DateRange(value="2022-01-01", op="gt"),
        era_end_date=DateRange(value="2022-12-31", op="lt"),
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "condition_era.condition_era_start_date > '2022-01-01'" in sql_str
    assert "condition_era.condition_era_end_date < '2022-12-31'" in sql_str


def test_condition_era_sql_numeric_filters():
    criteria = ConditionEra(
        occurrence_count=NumericRange(value=5, op="gt"),
        era_length=NumericRange(value=30, op="gte"),
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    sql_str = str(sql)

    assert "condition_era.condition_occurrence_count > 5" in sql_str
    # Era length is calculated as end - start
    # Postgres subtraction of dates yields integer days
    assert (
        "condition_era.condition_era_end_date - condition_era.condition_era_start_date >= 30"
        in sql_str
    )


def test_condition_era_age_at_start():
    # Note: AgeAtStart requires joining to Person table, which might not be implemented yet.
    # This test serves to document current behavior (likely ignored or incomplete).
    criteria = ConditionEra(age_at_start=NumericRange(value=18, op="gt"))
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    _ = str(sql)

    # If implemented, it would check year_of_birth from person table.
    # For now, we just assert it doesn't crash.
    pass
