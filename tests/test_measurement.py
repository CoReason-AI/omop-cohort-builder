from omop_cohort_builder.domain import Measurement, Criteria
from omop_cohort_builder.base import (
    NumericRange,
    DateRange,
    Concept,
    ConceptSetSelection,
)
from pydantic import TypeAdapter
import json


def test_measurement_serialization():
    m = Measurement(
        codeset_id=1,
        first=True,
        occurrence_start_date=DateRange(value="2023-01-01", op="gt"),
        measurement_type=[
            Concept(
                concept_id=3004249,
                concept_name="Blood pressure",
                concept_code="BP",
                domain_id="Measurement",
                vocabulary_id="LOINC",
                concept_class_id="Clinical Observation",
            )
        ],
        measurement_type_cs=ConceptSetSelection(codeset_id=2),
        measurement_type_exclude=True,
        value_as_number=NumericRange(value=120, op="gt"),
        range_low=NumericRange(value=60, op="lt"),
        abnormal=True,
    )
    dumped_json = m.model_dump_json(by_alias=True)
    dumped = json.loads(dumped_json)

    assert "Measurement" in dumped
    inner = dumped["Measurement"]

    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["OccurrenceStartDate"]["Value"] == "2023-01-01"
    assert inner["MeasurementType"][0]["CONCEPT_ID"] == 3004249
    assert inner["MeasurementTypeCS"]["CodesetId"] == 2
    assert inner["MeasurementTypeExclude"] is True
    assert inner["ValueAsNumber"]["Value"] == 120
    assert inner["RangeLow"]["Value"] == 60
    assert inner["Abnormal"] is True


def test_measurement_deserialization():
    json_data = """
    {
        "Measurement": {
            "CodesetId": 5,
            "MeasurementTypeCS": {"CodesetId": 10},
            "ValueAsNumber": {"Value": 5.5, "Op": "eq"},
            "Abnormal": false
        }
    }
    """
    # Use TypeAdapter(Criteria) to trigger the polymorphic deserializer (unwrapping)
    m = TypeAdapter(Criteria).validate_json(json_data)

    assert isinstance(m, Measurement)
    assert m.codeset_id == 5
    assert m.measurement_type_cs.codeset_id == 10
    assert m.value_as_number.value == 5.5
    assert m.abnormal is False


def test_measurement_defaults():
    m = Measurement()
    dumped = json.loads(m.model_dump_json(by_alias=True))
    inner = dumped["Measurement"]

    # Check that defaults are not serialized if None/exclude=True?
    # Actually Pydantic v2 dump exclude_none=False by default unless specified.
    # But in CirceModel/BaseCriteria we rely on default behaviors.
    # Checking specific default values from Java mapping if any.

    assert inner.get("MeasurementTypeExclude") is None
