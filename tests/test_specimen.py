from pydantic import TypeAdapter
from omop_cohort_builder.domain import Criteria, Specimen


def test_specimen_serialization():
    specimen = Specimen(
        codeset_id=1,
        first=True,
        specimen_type_exclude=True,
        specimen_source_concept=123,
    )

    # Test wrapping
    adapter = TypeAdapter(Criteria)
    json_output = adapter.dump_json(specimen, by_alias=True).decode()

    # The output should be wrapped
    assert '"Specimen":' in json_output
    assert '"criteria_type":' not in json_output
    assert '"CriteriaType":' not in json_output
    # Pydantic JSON dump might include spaces or not, so let's be flexible or check structural containment
    # "CodesetId":1 or "CodesetId": 1
    assert '"CodesetId":1' in json_output or '"CodesetId": 1' in json_output
    assert '"First":true' in json_output or '"First": true' in json_output
    assert (
        '"SpecimenTypeExclude":true' in json_output
        or '"SpecimenTypeExclude": true' in json_output
    )
    assert (
        '"SpecimenSourceConcept":123' in json_output
        or '"SpecimenSourceConcept": 123' in json_output
    )


def test_specimen_deserialization():
    json_input = """
    {
        "Specimen": {
            "CodesetId": 1,
            "First": true,
            "SpecimenTypeExclude": true,
            "SpecimenSourceConcept": 123,
            "SpecimenType": [{"CONCEPT_ID": 10, "CONCEPT_NAME": "Blood"}]
        }
    }
    """

    adapter = TypeAdapter(Criteria)
    criteria = adapter.validate_json(json_input)

    assert isinstance(criteria, Specimen)
    assert criteria.codeset_id == 1
    assert criteria.first is True
    assert criteria.specimen_type_exclude is True
    assert criteria.specimen_source_concept == 123
    assert criteria.specimen_type is not None
    assert len(criteria.specimen_type) == 1
    assert criteria.specimen_type[0].concept_id == 10


def test_specimen_full_fields():
    # Test all fields to ensure aliases are correct
    specimen = Specimen(
        codeset_id=1,
        first=False,
        specimen_type_exclude=False,
        specimen_source_concept=123,
    )

    # model_dump with by_alias=True on a WrappedCriteriaMixin returns the wrapped dict
    assert specimen.model_dump(by_alias=True, exclude_none=True) == {
        "Specimen": {
            "CodesetId": 1,
            "First": False,
            "SpecimenTypeExclude": False,
            "SpecimenSourceConcept": 123,
        }
    }
