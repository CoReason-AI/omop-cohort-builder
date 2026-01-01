import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select

from omop_cohort_builder.base import (
    TextFilter,
    NumericRange,
    DateRange,
    Concept,
)
from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DrugExposure


def compile_sql(query: Select) -> str:
    """Compiles the query to a string using the PostgreSQL dialect."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def normalize_sql(sql: str) -> str:
    """Normalizes SQL string by removing extra whitespace."""
    return " ".join(sql.split())


@pytest.fixture
def builder():
    return QueryBuilder()


def test_drug_exposure_basic(builder):
    criteria = DrugExposure()
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    expected = normalize_sql(
        "SELECT drug_exposure.drug_exposure_id, drug_exposure.person_id, drug_exposure.drug_concept_id, "
        "drug_exposure.drug_exposure_start_date, drug_exposure.drug_exposure_start_datetime, "
        "drug_exposure.drug_exposure_end_date, drug_exposure.drug_exposure_end_datetime, "
        "drug_exposure.verbatim_end_date, drug_exposure.drug_type_concept_id, drug_exposure.stop_reason, "
        "drug_exposure.refills, drug_exposure.quantity, drug_exposure.days_supply, drug_exposure.sig, "
        "drug_exposure.route_concept_id, drug_exposure.lot_number, drug_exposure.provider_id, "
        "drug_exposure.visit_occurrence_id, drug_exposure.visit_detail_id, drug_exposure.drug_source_value, "
        "drug_exposure.drug_source_concept_id, drug_exposure.route_source_value, drug_exposure.dose_unit_source_value "
        "FROM drug_exposure"
    )
    assert sql == expected


def test_drug_exposure_start_date(builder):
    criteria = DrugExposure(
        occurrence_start_date=DateRange(value="2023-01-01", op="gt")
    )
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.drug_exposure_start_date > '2023-01-01'" in sql


def test_drug_exposure_end_date(builder):
    criteria = DrugExposure(occurrence_end_date=DateRange(value="2023-12-31", op="lte"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.drug_exposure_end_date <= '2023-12-31'" in sql


def test_drug_exposure_drug_type(builder):
    criteria = DrugExposure(
        drug_type=[
            Concept(CONCEPT_ID=1, CONCEPT_NAME="Type A"),
            Concept(CONCEPT_ID=2, CONCEPT_NAME="Type B"),
        ]
    )
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.drug_type_concept_id IN (1, 2)" in sql


def test_drug_exposure_drug_type_exclude(builder):
    criteria = DrugExposure(
        drug_type=[
            Concept(CONCEPT_ID=1, CONCEPT_NAME="Type A"),
        ],
        drug_type_exclude=True,
    )
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.drug_type_concept_id NOT IN (1)" in sql


def test_drug_exposure_stop_reason(builder):
    criteria = DrugExposure(stop_reason=TextFilter(text="reason", op="contains"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    # SQLAlchemy escapes % as %% when literal_binds is True for some reason in tests context sometimes,
    # but here we rely on standard behavior.
    assert "drug_exposure.stop_reason LIKE '%%reason%%'" in sql


def test_drug_exposure_refills(builder):
    criteria = DrugExposure(refills=NumericRange(value=5, op="eq"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.refills = 5" in sql


def test_drug_exposure_quantity(builder):
    criteria = DrugExposure(quantity=NumericRange(value=10, op="gt"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.quantity > 10" in sql


def test_drug_exposure_days_supply(builder):
    criteria = DrugExposure(days_supply=NumericRange(value=30, op="gte"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.days_supply >= 30" in sql


def test_drug_exposure_route_concept(builder):
    criteria = DrugExposure(
        route_concept=[Concept(CONCEPT_ID=123, CONCEPT_NAME="Route")]
    )
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.route_concept_id IN (123)" in sql


def test_drug_exposure_lot_number(builder):
    criteria = DrugExposure(lot_number=TextFilter(text="LOT123", op="eq"))
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.lot_number = 'LOT123'" in sql


def test_drug_exposure_source_concept(builder):
    criteria = DrugExposure(drug_source_concept=456)
    query = builder.build_criteria(criteria)
    sql = normalize_sql(compile_sql(query))
    assert "drug_exposure.drug_source_concept_id = 456" in sql
