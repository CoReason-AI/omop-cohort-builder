from pydantic import TypeAdapter

from omop_cohort_builder.domain import (
    Criteria,
    DrugEra,
    NumericRange,
    DateRange,
    Concept,
    ConceptSetSelection,
)


class TestDrugEra:
    def test_drug_era_deserialization(self):
        json_data = {
            "DrugEra": {
                "CodesetId": 123,
                "First": True,
                "EraStartDate": {"Value": "2020-01-01", "Op": "gt"},
                "EraEndDate": {"Value": "2021-01-01", "Op": "lt"},
                "OccurrenceCount": {"Value": 1, "Op": "gt"},
                "EraLength": {"Value": 10, "Op": "gt"},
                "GapDays": {"Value": 5, "Op": "lt"},
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
        assert isinstance(criteria, DrugEra)
        assert criteria.codeset_id == 123
        assert criteria.first is True
        assert criteria.era_start_date.value == "2020-01-01"
        assert criteria.era_start_date.op == "gt"
        assert criteria.era_end_date.value == "2021-01-01"
        assert criteria.era_end_date.op == "lt"
        assert criteria.occurrence_count.value == 1
        assert criteria.occurrence_count.op == "gt"
        assert criteria.era_length.value == 10
        assert criteria.era_length.op == "gt"
        assert criteria.gap_days.value == 5
        assert criteria.gap_days.op == "lt"
        assert criteria.age_at_start.value == 18
        assert criteria.age_at_start.op == "gte"
        assert criteria.age_at_end.value == 65
        assert criteria.age_at_end.op == "lte"
        assert len(criteria.gender) == 1
        assert criteria.gender[0].concept_id == 8507
        assert criteria.gender_cs.codeset_id == 456

    def test_drug_era_serialization(self):
        drug_era = DrugEra(
            codeset_id=123,
            first=True,
            era_start_date=DateRange(value="2020-01-01", op="gt"),
            era_end_date=DateRange(value="2021-01-01", op="lt"),
            occurrence_count=NumericRange(value=1, op="gt"),
            era_length=NumericRange(value=10, op="gt"),
            gap_days=NumericRange(value=5, op="lt"),
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

        json_output = drug_era.model_dump(by_alias=True, exclude_none=True)
        expected_json = {
            "DrugEra": {
                "CodesetId": 123,
                "First": True,
                "EraStartDate": {"Value": "2020-01-01", "Op": "gt"},
                "EraEndDate": {"Value": "2021-01-01", "Op": "lt"},
                "OccurrenceCount": {"Value": 1, "Op": "gt"},
                "EraLength": {"Value": 10, "Op": "gt"},
                "GapDays": {"Value": 5, "Op": "lt"},
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

    def test_drug_era_minimal(self):
        """Test minimal instantiation"""
        drug_era = DrugEra()
        json_output = drug_era.model_dump(by_alias=True, exclude_none=True)
        assert json_output == {"DrugEra": {}}
