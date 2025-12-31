from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    Criteria,
    ConceptSetSelection,
    TextFilter,
)
from pydantic import TypeAdapter


def test_condition_occurrence_serialization():
    co = ConditionOccurrence(
        codeset_id=1, first=True, condition_type_cs=ConceptSetSelection(codeset_id=2)
    )

    # Test wrapper serialization
    dump = co.model_dump(by_alias=True)
    assert "ConditionOccurrence" in dump
    inner = dump["ConditionOccurrence"]
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["ConditionTypeCS"]["CodesetId"] == 2
    # Ensure discriminator is not present in inner dict
    assert "CriteriaType" not in inner
    assert "criteria_type" not in inner


def test_drug_exposure_serialization():
    de = DrugExposure(
        codeset_id=10,
        stop_reason=TextFilter(text="reason", op="eq"),
        drug_type_exclude=True,
    )
    dump = de.model_dump(by_alias=True)
    assert "DrugExposure" in dump
    inner = dump["DrugExposure"]
    assert inner["CodesetId"] == 10
    assert inner["DrugTypeExclude"] is True
    assert inner["StopReason"]["Text"] == "reason"


def test_criteria_polymorphism_deserialization():
    adapter = TypeAdapter(Criteria)

    # Test ConditionOccurrence
    data_co = {"ConditionOccurrence": {"CodesetId": 123, "First": True}}
    obj_co = adapter.validate_python(data_co)
    assert isinstance(obj_co, ConditionOccurrence)
    assert obj_co.codeset_id == 123
    assert obj_co.first is True

    # Test DrugExposure
    data_de = {"DrugExposure": {"CodesetId": 456, "DrugTypeExclude": True}}
    obj_de = adapter.validate_python(data_de)
    assert isinstance(obj_de, DrugExposure)
    assert obj_de.codeset_id == 456
    assert obj_de.drug_type_exclude is True


def test_criteria_round_trip():
    adapter = TypeAdapter(Criteria)

    co = ConditionOccurrence(codeset_id=999)
    dump = co.model_dump(by_alias=True)
    obj = adapter.validate_python(dump)
    assert isinstance(obj, ConditionOccurrence)
    assert obj.codeset_id == 999
