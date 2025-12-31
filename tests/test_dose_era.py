from pydantic import TypeAdapter

from omop_cohort_builder.domain import (
    Criteria,
    DoseEra,
    NumericRange,
    DateRange,
    Concept,
    ConceptSetSelection,
)


class TestDoseEra:
    def test_dose_era_deserialization(self):
        json_data = {
            "DoseEra": {
                "CodesetId": 123,
                "First": True,
                "EraStartDate": {"Value": "2020-01-01", "Op": "gt"},
                "EraEndDate": {"Value": "2021-01-01", "Op": "lt"},
                "Unit": [
                    {
                        "CONCEPT_ID": 9246,
                        "CONCEPT_NAME": "per gram",
                        "STANDARD_CONCEPT": "S",
                        "STANDARD_CONCEPT_CAPTION": "Standard",
                        "INVALID_REASON": "V",
                        "INVALID_REASON_CAPTION": "Valid",
                        "CONCEPT_CODE": "/g",
                        "DOMAIN_ID": "Unit",
                        "VOCABULARY_ID": "UCUM",
                        "CONCEPT_CLASS_ID": "Unit",
                    }
                ],
                "UnitCS": {"CodesetId": 789},
                "DoseValue": {"Value": 50, "Op": "gt"},
                "EraLength": {"Value": 10, "Op": "gt"},
                "AgeAtStart": {"Value": 18, "Op": "gte"},
                "AgeAtEnd": {"Value": 65, "Op": "lte"},
                "Gender": [
                    {
                        "CONCEPT_ID": 8507,
                        "CONCEPT_NAME": "MALE",
                        "STANDARD_CONCEPT": "S",
                        "STANDARD_CONCEPT_CAPTION": "Standard",
                        "INVALID_REASON": "V",
                        "INVALID_REASON_CAPTION": "Valid",
                        "CONCEPT_CODE": "M",
                        "DOMAIN_ID": "Gender",
                        "VOCABULARY_ID": "Gender",
                        "CONCEPT_CLASS_ID": "Gender",
                    }
                ],
                "GenderCS": {"CodesetId": 456},
            }
        }

        criteria = TypeAdapter(Criteria).validate_json(
            TypeAdapter(dict).dump_json(json_data)
        )
        assert isinstance(criteria, DoseEra)
        assert criteria.codeset_id == 123
        assert criteria.first is True
        assert criteria.era_start_date.value == "2020-01-01"
        assert criteria.era_start_date.op == "gt"
        assert criteria.era_end_date.value == "2021-01-01"
        assert criteria.era_end_date.op == "lt"
        assert len(criteria.unit) == 1
        assert criteria.unit[0].concept_id == 9246
        assert criteria.unit_cs.codeset_id == 789
        assert criteria.dose_value.value == 50
        assert criteria.dose_value.op == "gt"
        assert criteria.era_length.value == 10
        assert criteria.era_length.op == "gt"
        assert criteria.age_at_start.value == 18
        assert criteria.age_at_start.op == "gte"
        assert criteria.age_at_end.value == 65
        assert criteria.age_at_end.op == "lte"
        assert len(criteria.gender) == 1
        assert criteria.gender[0].concept_id == 8507
        assert criteria.gender_cs.codeset_id == 456

    def test_dose_era_serialization(self):
        dose_era = DoseEra(
            codeset_id=123,
            first=True,
            era_start_date=DateRange(value="2020-01-01", op="gt"),
            era_end_date=DateRange(value="2021-01-01", op="lt"),
            unit=[
                Concept(
                    concept_id=9246,
                    concept_name="per gram",
                    standard_concept="S",
                    standard_concept_caption="Standard",
                    invalid_reason="V",
                    invalid_reason_caption="Valid",
                    concept_code="/g",
                    domain_id="Unit",
                    vocabulary_id="UCUM",
                    concept_class_id="Unit",
                )
            ],
            unit_cs=ConceptSetSelection(codeset_id=789),
            dose_value=NumericRange(value=50, op="gt"),
            era_length=NumericRange(value=10, op="gt"),
            age_at_start=NumericRange(value=18, op="gte"),
            age_at_end=NumericRange(value=65, op="lte"),
            gender=[
                Concept(
                    concept_id=8507,
                    concept_name="MALE",
                    standard_concept="S",
                    standard_concept_caption="Standard",
                    invalid_reason="V",
                    invalid_reason_caption="Valid",
                    concept_code="M",
                    domain_id="Gender",
                    vocabulary_id="Gender",
                    concept_class_id="Gender",
                )
            ],
            gender_cs=ConceptSetSelection(codeset_id=456),
        )

        json_output = dose_era.model_dump(by_alias=True, exclude_none=True)
        expected_json = {
            "DoseEra": {
                "CodesetId": 123,
                "First": True,
                "EraStartDate": {"Value": "2020-01-01", "Op": "gt"},
                "EraEndDate": {"Value": "2021-01-01", "Op": "lt"},
                "Unit": [
                    {
                        "CONCEPT_ID": 9246,
                        "CONCEPT_NAME": "per gram",
                        "STANDARD_CONCEPT": "S",
                        "STANDARD_CONCEPT_CAPTION": "Standard",
                        "INVALID_REASON": "V",
                        "INVALID_REASON_CAPTION": "Valid",
                        "CONCEPT_CODE": "/g",
                        "DOMAIN_ID": "Unit",
                        "VOCABULARY_ID": "UCUM",
                        "CONCEPT_CLASS_ID": "Unit",
                    }
                ],
                "UnitCS": {"CodesetId": 789},
                "DoseValue": {"Value": 50, "Op": "gt"},
                "EraLength": {"Value": 10, "Op": "gt"},
                "AgeAtStart": {"Value": 18, "Op": "gte"},
                "AgeAtEnd": {"Value": 65, "Op": "lte"},
                "Gender": [
                    {
                        "CONCEPT_ID": 8507,
                        "CONCEPT_NAME": "MALE",
                        "STANDARD_CONCEPT": "S",
                        "STANDARD_CONCEPT_CAPTION": "Standard",
                        "INVALID_REASON": "V",
                        "INVALID_REASON_CAPTION": "Valid",
                        "CONCEPT_CODE": "M",
                        "DOMAIN_ID": "Gender",
                        "VOCABULARY_ID": "Gender",
                        "CONCEPT_CLASS_ID": "Gender",
                    }
                ],
                "GenderCS": {"CodesetId": 456},
            }
        }
        assert json_output == expected_json

    def test_dose_era_minimal(self):
        """Test minimal instantiation"""
        dose_era = DoseEra()
        json_output = dose_era.model_dump(by_alias=True, exclude_none=True)
        assert json_output == {"DoseEra": {}}
