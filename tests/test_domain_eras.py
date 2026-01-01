from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    ConditionEra,
    DrugEra,
    DoseEra,
    Criteria,
)
from omop_cohort_builder.base import NumericRange, ConceptSetSelection


def test_condition_era_deserialization():
    json_data = """
    {
        "ConditionEra": {
            "CodesetId": 1,
            "First": true,
            "EraStartDate": {"Value": "2020-01-01", "Op": "gt"},
            "EraEndDate": {"Value": "2020-12-31", "Op": "lt"},
            "OccurrenceCount": {"Value": 1, "Op": "gt"},
            "EraLength": {"Value": 30, "Op": "gt"},
            "AgeAtStart": {"Value": 18, "Op": "gt"},
            "AgeAtEnd": {"Value": 65, "Op": "lt"},
            "Gender": [{"CONCEPT_ID": 8507, "CONCEPT_NAME": "Male"}],
            "GenderCS": {"CodesetId": 2}
        }
    }
    """
    adapter = TypeAdapter(Criteria)
    criteria = adapter.validate_json(json_data)

    assert isinstance(criteria, ConditionEra)
    assert criteria.codeset_id == 1
    assert criteria.first is True
    assert criteria.era_start_date.value == "2020-01-01"
    assert criteria.era_end_date.value == "2020-12-31"
    assert criteria.occurrence_count.value == 1
    assert criteria.era_length.value == 30
    assert criteria.age_at_start.value == 18
    assert criteria.age_at_end.value == 65
    assert len(criteria.gender) == 1
    assert criteria.gender[0].concept_id == 8507
    assert criteria.gender_cs.codeset_id == 2


def test_drug_era_deserialization():
    json_data = """
    {
        "DrugEra": {
            "CodesetId": 10,
            "First": false,
            "GapDays": {"Value": 5, "Op": "lt"},
            "GenderCS": {"CodesetId": 20}
        }
    }
    """
    adapter = TypeAdapter(Criteria)
    criteria = adapter.validate_json(json_data)

    assert isinstance(criteria, DrugEra)
    assert criteria.codeset_id == 10
    assert criteria.first is False
    assert criteria.gap_days.value == 5
    assert criteria.gender_cs.codeset_id == 20


def test_dose_era_deserialization():
    json_data = """
    {
        "DoseEra": {
            "CodesetId": 30,
            "Unit": [{"CONCEPT_ID": 123, "CONCEPT_NAME": "mg"}],
            "UnitCS": {"CodesetId": 40},
            "DoseValue": {"Value": 500, "Op": "eq"}
        }
    }
    """
    adapter = TypeAdapter(Criteria)
    criteria = adapter.validate_json(json_data)

    assert isinstance(criteria, DoseEra)
    assert criteria.codeset_id == 30
    assert len(criteria.unit) == 1
    assert criteria.unit[0].concept_id == 123
    assert criteria.unit_cs.codeset_id == 40
    assert criteria.dose_value.value == 500


def test_serialization_round_trip():
    era = DrugEra(
        codeset_id=1,
        gap_days=NumericRange(value=10, op="gt"),
        gender_cs=ConceptSetSelection(codeset_id=5),
    )

    dumped = era.model_dump(by_alias=True, exclude_none=True)
    expected_key = "DrugEra"
    assert expected_key in dumped
    data = dumped[expected_key]

    assert data["CodesetId"] == 1
    assert data["GapDays"] == {"Value": 10, "Op": "gt"}
    assert data["GenderCS"] == {"CodesetId": 5}
    # Verify PascalCase alias for CS field
    assert "GenderCS" in data
    assert "gender_cs" not in data
