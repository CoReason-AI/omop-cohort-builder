from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    Concept,
    ConceptSetSelection,
    Criteria,
)
from omop_cohort_builder.core import (
    TextFilter,
    NumericRange,
    DateRange,
    DateAdjustment,
    DateAdjustmentType,
)
from pydantic import TypeAdapter
import json


def test_condition_occurrence_serialization():
    # Arrange
    criteria = ConditionOccurrence(
        codeset_id=1,
        first=True,
        occurrence_start_date=DateRange(value="2023-01-01", op="gt"),
        occurrence_end_date=DateRange(value="2023-12-31", op="lt"),
        condition_type=[
            Concept(concept_id=1, concept_name="Test Concept", standard_concept="S")
        ],
        condition_type_cs=ConceptSetSelection(codeset_id=10, is_exclusion=True),
        condition_type_exclude=False,
        stop_reason=TextFilter(text="Healed", op="eq"),
        condition_source_concept=12345,
        age=NumericRange(value=30, op="gt"),
        gender=[Concept(concept_id=8507, concept_name="Male")],
        gender_cs=ConceptSetSelection(codeset_id=20),
        provider_specialty=[Concept(concept_id=30, concept_name="Cardiology")],
        provider_specialty_cs=ConceptSetSelection(codeset_id=30),
        visit_type=[Concept(concept_id=9201, concept_name="Inpatient")],
        visit_type_cs=ConceptSetSelection(codeset_id=40),
        condition_status=[Concept(concept_id=100, concept_name="Active")],
        condition_status_cs=ConceptSetSelection(codeset_id=50),
        date_adjustment=DateAdjustment(
            start_with=DateAdjustmentType.START_DATE,
            start_offset=1,
            end_with=DateAdjustmentType.END_DATE,
            end_offset=1,
        ),
    )

    # Act
    # We dump with by_alias=True to get PascalCase keys
    # We verify the wrapped behavior via model_dump (which triggers the serializer)
    json_output = criteria.model_dump_json(by_alias=True)
    data = json.loads(json_output)

    # Assert
    # The WrappedCriteriaMixin should wrap the output in "ConditionOccurrence"
    assert "ConditionOccurrence" in data
    inner = data["ConditionOccurrence"]

    # Check top-level fields match Java @JsonProperty
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["ConditionTypeExclude"] is False
    assert inner["ConditionSourceConcept"] == 12345

    # Check complex objects
    assert inner["OccurrenceStartDate"] == {
        "Value": "2023-01-01",
        "Op": "gt",
        "Extent": None,
    }
    assert inner["OccurrenceEndDate"] == {
        "Value": "2023-12-31",
        "Op": "lt",
        "Extent": None,
    }

    assert len(inner["ConditionType"]) == 1
    assert inner["ConditionType"][0]["CONCEPT_ID"] == 1
    assert inner["ConditionType"][0]["CONCEPT_NAME"] == "Test Concept"

    assert inner["ConditionTypeCS"] == {"CodesetId": 10, "IsExclusion": True}

    assert inner["StopReason"] == {"Text": "Healed", "Op": "eq"}
    assert inner["Age"] == {"Value": 30.0, "Op": "gt", "Extent": None}

    assert inner["GenderCS"] == {"CodesetId": 20, "IsExclusion": False}

    assert inner["DateAdjustment"] == {
        "StartWith": "START_DATE",
        "StartOffset": 1,
        "EndWith": "END_DATE",
        "EndOffset": 1,
    }

    # IMPORTANT: Ensure the discriminator "CriteriaType" is NOT inside the wrapper
    # as per the `WrappedCriteriaMixin` logic which deletes it.
    assert "CriteriaType" not in inner
    assert "criteria_type" not in inner


def test_drug_exposure_serialization():
    # Arrange
    criteria = DrugExposure(
        codeset_id=2,
        first=False,
        occurrence_start_date=DateRange(value="2023-01-01", op="eq"),
        drug_type=[Concept(concept_id=2, concept_name="Drug Type")],
        refills=NumericRange(value=0, op="eq"),
        quantity=NumericRange(value=10, op="gt"),
        days_supply=NumericRange(value=30, op="eq"),
        route_concept=[Concept(concept_id=3, concept_name="Route")],
        effective_drug_dose=NumericRange(value=500, op="eq"),
        dose_unit=[Concept(concept_id=4, concept_name="mg")],
        lot_number=TextFilter(text="LOT123", op="eq"),
        drug_source_concept=54321,
    )

    # Act
    json_output = criteria.model_dump_json(by_alias=True)
    data = json.loads(json_output)

    # Assert
    assert "DrugExposure" in data
    inner = data["DrugExposure"]

    assert inner["CodesetId"] == 2
    assert inner["First"] is False
    assert inner["Refills"] == {"Value": 0.0, "Op": "eq", "Extent": None}
    assert inner["Quantity"] == {"Value": 10.0, "Op": "gt", "Extent": None}
    assert inner["DaysSupply"] == {"Value": 30.0, "Op": "eq", "Extent": None}
    assert inner["EffectiveDrugDose"] == {"Value": 500.0, "Op": "eq", "Extent": None}
    assert inner["LotNumber"] == {"Text": "LOT123", "Op": "eq"}
    assert inner["DrugSourceConcept"] == 54321


def test_criteria_deserialization():
    # 1. Test Wrapped Object (Standard OHDSI format)
    json_input = """
    {
        "ConditionOccurrence": {
            "CodesetId": 1,
            "First": true,
            "OccurrenceStartDate": {"Value": "2023-01-01", "Op": "gt"}
        }
    }
    """
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_json(json_input)

    assert isinstance(obj, ConditionOccurrence)
    assert obj.codeset_id == 1
    assert obj.first is True
    assert obj.occurrence_start_date.value == "2023-01-01"

    # 2. Test Unwraped Object (Direct dict with discriminator - e.g. internal usage)
    # The criteria_deserializer should return 'v' as is, and Pydantic discriminator should work
    json_input_unwrapped = """
    {
        "CriteriaType": "DrugExposure",
        "CodesetId": 2,
        "Refills": {"Value": 0, "Op": "eq"}
    }
    """
    obj2 = adapter.validate_json(json_input_unwrapped)
    assert isinstance(obj2, DrugExposure)
    assert obj2.codeset_id == 2
    assert obj2.refills.value == 0

    # 3. Test non-dict input (pass-through coverage)
    # This won't validate as Criteria, but it exercises the deserializer code path
    from omop_cohort_builder.domain import criteria_deserializer

    assert criteria_deserializer("string") == "string"
    assert criteria_deserializer({"A": 1, "B": 2}) == {"A": 1, "B": 2}  # >1 key
    assert criteria_deserializer({"A": 1}) == {"A": 1}  # 1 key, but value not dict


def test_serialization_by_alias_false():
    # Covers the path where "criteria_type" (snake_case) might be present
    criteria = ConditionOccurrence(codeset_id=1)

    # When dumping by_alias=False, fields are snake_case.
    # The mixin should still wrap it and remove 'criteria_type'.
    data = criteria.model_dump(by_alias=False)

    assert "ConditionOccurrence" in data
    inner = data["ConditionOccurrence"]

    # Keys should be snake_case
    assert "codeset_id" in inner
    assert inner["codeset_id"] == 1

    # Discriminator should be removed
    assert "criteria_type" not in inner
    assert "CriteriaType" not in inner
