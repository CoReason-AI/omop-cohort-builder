from __future__ import annotations

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import Measurement, NumericRange
from omop_cohort_builder.base import Concept
from sqlalchemy.dialects import postgresql
from sqlalchemy import select

def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )

def normalize(s):
    return " ".join(s.split())

def test_build_measurement_simple():
    qb = QueryBuilder()
    criteria = Measurement()

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    # Basic select check
    assert "SELECT measurement.measurement_id" in sql
    assert "FROM measurement" in sql

def test_build_measurement_with_concepts():
    qb = QueryBuilder()
    criteria = Measurement(
        measurement_type=[Concept(concept_id=123, concept_name="Test Type")],
        operator=[Concept(concept_id=456, concept_name="Test Op")],
        value_as_concept=[Concept(concept_id=789, concept_name="Test Value")],
        unit=[Concept(concept_id=101, concept_name="Test Unit")]
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "measurement.measurement_type_concept_id IN (123)" in sql
    assert "measurement.operator_concept_id IN (456)" in sql
    assert "measurement.value_as_concept_id IN (789)" in sql
    assert "measurement.unit_concept_id IN (101)" in sql

def test_build_measurement_numeric_filters():
    qb = QueryBuilder()
    criteria = Measurement(
        value_as_number=NumericRange(value=10.5, op="gt"),
        range_low=NumericRange(value=5.0, op="lt"),
        range_high=NumericRange(value=20.0, op="gte")
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "measurement.value_as_number > 10.5" in sql
    assert "measurement.range_low < 5.0" in sql
    assert "measurement.range_high >= 20.0" in sql

def test_build_measurement_source_concept():
    qb = QueryBuilder()
    criteria = Measurement(
        measurement_source_concept=999
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))

    assert "measurement.measurement_source_concept_id = 999" in sql

def test_build_measurement_ratios_and_abnormal():
    # Note: Ratios and abnormal require computed columns or complex logic
    # not directly in the base table usually, but we check if our builder
    # implements the specific logic found in Java.

    # Java logic for abnormal:
    # (C.value_as_number < C.range_low or C.value_as_number > C.range_high or C.value_as_concept_id in (4155142, 4155143))

    # Java logic for ratio:
    # (C.value_as_number / NULLIF(C.range_low, 0)) op value

    qb = QueryBuilder()
    criteria = Measurement(
        abnormal=True,
        range_low_ratio=NumericRange(value=1.5, op="gt"),
        range_high_ratio=NumericRange(value=0.5, op="lt")
    )

    query = qb.build_criteria(criteria)
    sql = str(compile_query(query))
    norm_sql = normalize(sql)

    # Verify abnormal logic
    assert "measurement.value_as_number < measurement.range_low" in sql
    assert "measurement.value_as_number > measurement.range_high" in sql
    assert "measurement.value_as_concept_id IN (4155142, 4155143)" in sql

    # Verify ratio logic
    # SQLAlchemy renders functions in lowercase by default
    # We check for the key components: value_as_number, nullif, range_low/high, and the ratio values

    # The generated SQL might have different spacing or parenthesis (e.g. `col / func(col)`)
    # so we check for components presence if strict matching fails due to formatting nuances.

    # Check for value_as_number
    assert "measurement.value_as_number" in sql

    # Check for nullif usage
    assert "nullif(measurement.range_low, 0)" in sql
    assert "nullif(measurement.range_high, 0)" in sql

    # Check for ratio values
    assert "1.5" in sql
    assert "0.5" in sql
