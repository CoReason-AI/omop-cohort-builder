import pytest
from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    Criteria,
    ConditionOccurrence,
    DrugExposure,
    VisitOccurrence,
    ConceptSetSelection,
    NumericRange,
    DateRange,
)


def test_condition_occurrence_serialization():
    co = ConditionOccurrence(
        codeset_id=1,
        first=True,
        occurrence_start_date=DateRange(value="2023-01-01", op="gt"),
        condition_type_cs=ConceptSetSelection(codeset_id=2),
    )

    # Direct model dump
    data = co.model_dump(by_alias=True, exclude_none=True)
    # WrappedCriteriaMixin should wrap it
    assert "ConditionOccurrence" in data
    inner = data["ConditionOccurrence"]
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["OccurrenceStartDate"] == {"Value": "2023-01-01", "Op": "gt"}
    assert inner["ConditionTypeCS"] == {"CodesetId": 2}
    assert "CriteriaType" not in inner  # Should be excluded


def test_condition_occurrence_deserialization():
    json_str = """
    {
        "ConditionOccurrence": {
            "CodesetId": 1,
            "First": true,
            "OccurrenceStartDate": {"Value": "2023-01-01", "Op": "gt"},
            "ConditionTypeCS": {"CodesetId": 2}
        }
    }
    """
    # Use TypeAdapter(Criteria) to trigger the union logic and BeforeValidator
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_json(json_str)

    assert isinstance(obj, ConditionOccurrence)
    assert obj.codeset_id == 1
    assert obj.first is True
    assert obj.occurrence_start_date.value == "2023-01-01"


def test_drug_exposure_serialization():
    de = DrugExposure(
        codeset_id=10, drug_type_exclude=True, quantity=NumericRange(value=5, op="gt")
    )
    data = de.model_dump(by_alias=True, exclude_none=True)
    assert "DrugExposure" in data
    inner = data["DrugExposure"]
    assert inner["CodesetId"] == 10
    assert inner["DrugTypeExclude"] is True
    assert inner["Quantity"] == {"Value": 5, "Op": "gt"}


def test_visit_occurrence_polymorphism():
    # Test that we can parse different types via the Union
    json_list = [
        {"ConditionOccurrence": {"CodesetId": 1}},
        {"VisitOccurrence": {"CodesetId": 2, "PlaceOfServiceLocation": 123}},
    ]

    adapter = TypeAdapter(list[Criteria])
    objects = adapter.validate_python(json_list)

    assert len(objects) == 2
    assert isinstance(objects[0], ConditionOccurrence)
    assert objects[0].codeset_id == 1

    assert isinstance(objects[1], VisitOccurrence)
    assert objects[1].codeset_id == 2
    assert objects[1].place_of_service_location == 123


def test_unwrapped_deserialization_failure():
    # If we pass unwrapped dict without discriminator, it might fail or pick one if strictness is loose.
    # But our BeforeValidator expects the wrapper key or existing criteria_type.
    # If we pass {"CodesetId": 1}, it doesn't know what it is.

    json_str = '{"CodesetId": 1}'
    adapter = TypeAdapter(Criteria)
    with pytest.raises(Exception):
        adapter.validate_json(json_str)


def test_criteria_snake_case_conversion():
    # Verify that snake_case args in constructor work and map to PascalCase json
    co = ConditionOccurrence(condition_source_concept=999)
    data = co.model_dump(by_alias=True, exclude_none=True)
    assert data["ConditionOccurrence"]["ConditionSourceConcept"] == 999
