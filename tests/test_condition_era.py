from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    ConditionEra,
    Criteria,
    Concept,
    DateRange,
    NumericRange,
)
from omop_cohort_builder.base import ConceptSetSelection


def test_condition_era_instantiation():
    ce = ConditionEra()
    assert ce.criteria_type == "ConditionEra"
    assert ce.codeset_id is None


def test_condition_era_fields():
    ce = ConditionEra(
        codeset_id=1,
        first=True,
        era_start_date=DateRange(value="2020-01-01", op="gt"),
        era_end_date=DateRange(value="2020-12-31", op="lt"),
        occurrence_count=NumericRange(value=1, op="eq"),
        era_length=NumericRange(value=30, op="gt"),
        age_at_start=NumericRange(value=18, op="gt"),
        age_at_end=NumericRange(value=65, op="lt"),
        gender=[Concept(concept_id=8507, concept_name="Male")],
        gender_cs=ConceptSetSelection(codeset_id=2),
    )
    assert ce.codeset_id == 1
    assert ce.first is True
    assert ce.era_start_date.value == "2020-01-01"
    assert ce.gender[0].concept_id == 8507
    assert ce.gender_cs.codeset_id == 2


def test_condition_era_serialization():
    ce = ConditionEra(codeset_id=1, first=True)
    # Use TypeAdapter to test union serialization if needed, but here testing the model directly
    # Wrapped serialization is handled by the mixin
    data = ce.model_dump(by_alias=True, exclude_none=True)
    # The mixin wraps it
    assert "ConditionEra" in data
    inner = data["ConditionEra"]
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert "CriteriaType" not in inner


def test_condition_era_deserialization_wrapped():
    json_data = """
    {
        "ConditionEra": {
            "CodesetId": 123,
            "First": true,
            "EraStartDate": {"Value": "2022-01-01", "Op": "eq"}
        }
    }
    """
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_json(json_data)
    assert isinstance(obj, ConditionEra)
    assert obj.criteria_type == "ConditionEra"
    assert obj.codeset_id == 123
    assert obj.first is True
    assert obj.era_start_date.value == "2022-01-01"


def test_condition_era_deserialization_wrapped_with_type_discriminator():
    # Test if the json has extra fields that should be ignored or if it works with CriteriaType if present (though it shouldn't be for deserialization usually)
    pass
