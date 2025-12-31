from omop_cohort_builder.domain import DemographicCriteria
from omop_cohort_builder.base import NumericRange, DateRange


def test_demographic_criteria_fields():
    """
    Test that DemographicCriteria can be instantiated with all expected fields
    and that they serialize to the correct PascalCase/Aliased JSON keys.
    """
    data = {
        "Age": {"Value": 18, "Op": "gte"},
        "Gender": [{"CONCEPT_ID": 8507, "CONCEPT_NAME": "MALE"}],
        "GenderCS": {"CodesetId": 1},
        "Race": [{"CONCEPT_ID": 8527, "CONCEPT_NAME": "WHITE"}],
        "RaceCS": {"CodesetId": 2},
        "Ethnicity": [{"CONCEPT_ID": 38003563, "CONCEPT_NAME": "HISPANIC"}],
        "EthnicityCS": {"CodesetId": 3},
        "OccurrenceStartDate": {"Value": "2020-01-01", "Op": "gt"},
        "OccurrenceEndDate": {"Value": "2020-12-31", "Op": "lt"},
    }

    # Deserialization check
    model = DemographicCriteria.model_validate(data)

    assert model.age is not None
    assert isinstance(model.age, NumericRange)
    assert model.age.value == 18
    assert model.age.op == "gte"

    assert model.gender is not None
    assert len(model.gender) == 1
    assert model.gender[0].concept_id == 8507

    assert model.gender_cs is not None
    assert model.gender_cs.codeset_id == 1

    assert model.race is not None
    assert model.race[0].concept_name == "WHITE"

    assert model.race_cs is not None
    assert model.race_cs.codeset_id == 2

    assert model.ethnicity is not None
    assert model.ethnicity[0].concept_id == 38003563

    assert model.ethnicity_cs is not None
    assert model.ethnicity_cs.codeset_id == 3

    assert model.occurrence_start_date is not None
    assert isinstance(model.occurrence_start_date, DateRange)
    assert model.occurrence_start_date.value == "2020-01-01"

    assert model.occurrence_end_date is not None
    assert model.occurrence_end_date.value == "2020-12-31"

    # Serialization check
    dump = model.model_dump(by_alias=True, exclude_none=True)
    assert "Age" in dump
    assert "Gender" in dump
    assert "GenderCS" in dump  # Ensure CS alias works
    assert "Race" in dump
    assert "RaceCS" in dump
    assert "Ethnicity" in dump
    assert "EthnicityCS" in dump
    assert "OccurrenceStartDate" in dump
    assert "OccurrenceEndDate" in dump


def test_demographic_criteria_empty():
    """Test that fields are optional."""
    model = DemographicCriteria()
    assert model.age is None
    dump = model.model_dump(by_alias=True, exclude_none=True)
    assert dump == {}
