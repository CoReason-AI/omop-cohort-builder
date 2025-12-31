from pydantic import TypeAdapter
from omop_cohort_builder.domain import Criteria


def test_observation_deserialization():
    json_data = {
        "Observation": {
            "CodesetId": 0,
            "OccurrenceStartDate": {"Value": "2015-10-01", "Op": "gte"},
            "ObservationType": [
                {
                    "CONCEPT_CODE": "OMOP generated",
                    "CONCEPT_ID": 42865906,
                    "CONCEPT_NAME": "Condition Procedure",
                    "DOMAIN_ID": "Type Concept",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "Procedure Type",
                }
            ],
            "ValueAsNumber": {"Value": 30, "Op": "lt"},
            "ValueAsString": {"Text": "obs value suffix", "Op": "endsWith"},
            "ValueAsConcept": [
                {
                    "CONCEPT_CODE": "10828004",
                    "CONCEPT_ID": 9191,
                    "CONCEPT_NAME": "Positive",
                    "DOMAIN_ID": "Meas Value",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "SNOMED",
                }
            ],
            "Qualifier": [
                {
                    "CONCEPT_CODE": "0001",
                    "CONCEPT_ID": 38003025,
                    "CONCEPT_NAME": "Total Charge",
                    "DOMAIN_ID": "Revenue Code",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "Revenue Code",
                }
            ],
            "Unit": [
                {
                    "CONCEPT_CODE": "/100",
                    "CONCEPT_ID": 9243,
                    "CONCEPT_NAME": "per hundred",
                    "DOMAIN_ID": "Unit",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "UCUM",
                }
            ],
            "First": True,
            "Age": {"Value": 18, "Op": "gt"},
            "Gender": [
                {
                    "CONCEPT_CODE": "F",
                    "CONCEPT_ID": 8532,
                    "CONCEPT_NAME": "FEMALE",
                    "DOMAIN_ID": "Gender",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "Gender",
                }
            ],
            "ProviderSpecialty": [
                {
                    "CONCEPT_CODE": "03...13",
                    "CONCEPT_ID": 45421646,
                    "CONCEPT_NAME": "Health profession",
                    "DOMAIN_ID": "Provider Specialty",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "Read",
                }
            ],
            "VisitType": [
                {
                    "CONCEPT_CODE": "ER",
                    "CONCEPT_ID": 9203,
                    "CONCEPT_NAME": "Emergency Room Visit",
                    "DOMAIN_ID": "Visit",
                    "INVALID_REASON_CAPTION": "Unknown",
                    "STANDARD_CONCEPT_CAPTION": "Unknown",
                    "VOCABULARY_ID": "Visit",
                }
            ],
        }
    }

    # Deserialization
    adapter = TypeAdapter(Criteria)
    observation = adapter.validate_python(json_data)

    assert observation.codeset_id == 0
    assert observation.occurrence_start_date.value == "2015-10-01"
    assert observation.occurrence_start_date.op == "gte"

    assert len(observation.observation_type) == 1
    assert observation.observation_type[0].concept_id == 42865906

    assert observation.value_as_number.value == 30
    assert observation.value_as_number.op == "lt"

    assert observation.value_as_string.text == "obs value suffix"
    assert observation.value_as_string.op == "endsWith"

    assert len(observation.value_as_concept) == 1
    assert observation.value_as_concept[0].concept_name == "Positive"

    assert len(observation.qualifier) == 1
    assert observation.qualifier[0].concept_name == "Total Charge"

    assert len(observation.unit) == 1
    assert observation.unit[0].concept_name == "per hundred"

    assert observation.first is True

    assert observation.age.value == 18
    assert observation.age.op == "gt"

    assert len(observation.gender) == 1
    assert observation.gender[0].concept_name == "FEMALE"

    assert len(observation.provider_specialty) == 1
    assert observation.provider_specialty[0].concept_name == "Health profession"

    assert len(observation.visit_type) == 1
    assert observation.visit_type[0].concept_name == "Emergency Room Visit"

    # Serialization
    serialized = adapter.dump_python(observation, by_alias=True, exclude_none=True)

    # Check wrapper
    assert "Observation" in serialized
    obs_dict = serialized["Observation"]

    assert obs_dict["CodesetId"] == 0
    assert obs_dict["ValueAsNumber"]["Value"] == 30
    assert obs_dict["ValueAsString"]["Text"] == "obs value suffix"
    assert obs_dict["Qualifier"][0]["CONCEPT_ID"] == 38003025
    assert obs_dict["Unit"][0]["CONCEPT_ID"] == 9243
