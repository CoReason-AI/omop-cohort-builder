import json
from pydantic import TypeAdapter
from src.omop_cohort_builder.domain import ConditionOccurrence, Criteria, DrugExposure, PrimaryCriteria, ObservationFilter, ResultLimit, criteria_deserializer

def test_condition_occurrence_serialization():
    json_data = {
        "ConditionOccurrence": {
            "CodesetId": 1,
            "First": True,
            "Age": {
                "Value": 25,
                "Op": "gt"
            }
        }
    }

    # Deserialize
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_python(json_data)
    assert isinstance(obj, ConditionOccurrence)
    assert obj.codeset_id == 1
    assert obj.first is True
    assert obj.age.value == 25
    assert obj.age.op == "gt"
    assert obj.criteria_type == "ConditionOccurrence"

    # Serialize
    output_json = adapter.dump_python(obj, by_alias=True, exclude_none=True)
    assert output_json == json_data

def test_drug_exposure_serialization():
    json_data = {
        "DrugExposure": {
            "CodesetId": 2,
            "DrugTypeExclude": False,
            "Refills": {
                "Value": 1,
                "Op": "eq"
            }
        }
    }

    # Deserialize
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_python(json_data)
    assert isinstance(obj, DrugExposure)
    assert obj.codeset_id == 2
    assert obj.refills.value == 1

    # Serialize
    output_json = adapter.dump_python(obj, by_alias=True, exclude_none=True)
    assert output_json == json_data

def test_primary_criteria_serialization():
    json_data = {
        "CriteriaList": [
            {
                "ConditionOccurrence": {
                    "CodesetId": 1
                }
            },
            {
                "DrugExposure": {
                    "CodesetId": 2,
                    "DrugTypeExclude": False
                }
            }
        ],
        "ObservationWindow": {
            "PriorDays": 365,
            "PostDays": 0
        },
        "PrimaryCriteriaLimit": {
            "Type": "First"
        }
    }

    obj = PrimaryCriteria.model_validate(json_data)
    assert len(obj.criteria_list) == 2
    assert isinstance(obj.criteria_list[0], ConditionOccurrence)
    assert isinstance(obj.criteria_list[1], DrugExposure)
    assert obj.observation_window.prior_days == 365

    output_json = obj.model_dump(by_alias=True, exclude_none=True)
    assert output_json == json_data

def test_internal_serialization():
    # Test serialization by_alias=False (Pythonic names)
    obj = ConditionOccurrence(codeset_id=99)
    dump = obj.model_dump(by_alias=False, exclude_none=True)

    assert "ConditionOccurrence" in dump
    inner = dump["ConditionOccurrence"]
    assert "codeset_id" in inner
    assert inner["codeset_id"] == 99
    assert "criteria_type" not in inner

def test_criteria_deserializer_direct():
    input_data = {"ConditionOccurrence": {"CodesetId": 1}}
    output = criteria_deserializer(input_data)
    assert output["criteria_type"] == "ConditionOccurrence"
    assert output["CodesetId"] == 1

    # Test passthrough
    assert criteria_deserializer("foo") == "foo"
    assert criteria_deserializer({}) == {}
    assert criteria_deserializer({"A": 1, "B": 2}) == {"A": 1, "B": 2}
    assert criteria_deserializer({"A": "not dict"}) == {"A": "not dict"}
