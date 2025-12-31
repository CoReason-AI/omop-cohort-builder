from __future__ import annotations

from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import DeviceExposure
from omop_cohort_builder.base import TextFilter, NumericRange, Concept, DateRange


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_device_exposure_basic():
    """Test DeviceExposure query generation without filters."""
    criteria = DeviceExposure()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT device_exposure.device_exposure_id" in sql
    assert "FROM device_exposure" in sql


def test_device_exposure_concept_filters():
    """Test DeviceExposure query generation with concept filters."""
    c1 = Concept(
        CONCEPT_ID=101,
        CONCEPT_NAME="Implant",
        DOMAIN_ID="Device",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Device",
    )
    criteria = DeviceExposure(device_type=[c1])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "device_exposure.device_type_concept_id IN (101)" in sql


def test_device_exposure_scalar_filters():
    """Test DeviceExposure with scalar filters."""
    criteria = DeviceExposure(
        unique_device_id=TextFilter(text="UDI123", op="eq"),
        quantity=NumericRange(value=5, op="gte"),
        device_source_concept=202,
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "device_exposure.unique_device_id = 'UDI123'" in sql
    assert "device_exposure.quantity >= 5" in sql
    assert "device_exposure.device_source_concept_id = 202" in sql


def test_device_exposure_date_filters():
    """Test DeviceExposure with date filters."""
    criteria = DeviceExposure(
        occurrence_start_date=DateRange(value="2022-01-01", op="gt"),
        occurrence_end_date=DateRange(value="2022-12-31", op="lt"),
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "device_exposure.device_exposure_start_date > '2022-01-01'" in sql
    assert "device_exposure.device_exposure_end_date < '2022-12-31'" in sql
