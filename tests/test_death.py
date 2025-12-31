from omop_cohort_builder.domain import Death, Criteria
from omop_cohort_builder.base import Concept, NumericRange
from pydantic import TypeAdapter
import json


def test_death_serialization():
    death = Death(codeset_id=1, death_type_exclude=True, death_source_concept=12345)

    # Wrapped serialization test
    json_output = death.model_dump_json(by_alias=True)
    # Check strict wrapper serialization
    data = json.loads(json_output)
    assert "Death" in data
    assert data["Death"]["CodesetId"] == 1
    assert data["Death"]["DeathTypeExclude"] is True

    # Deserialization test
    obj = TypeAdapter(Criteria).validate_python(data)
    assert isinstance(obj, Death)
    assert obj.codeset_id == 1
    assert obj.death_type_exclude is True


def test_death_full_fields():
    death = Death(
        codeset_id=10,
        age=NumericRange(value=50, op="gt"),
        gender=[Concept(alias="CONCEPT_ID", concept_id=123, concept_name="Male")],
    )

    # Re-instantiate Concept correctly using names
    c = Concept(concept_id=123, concept_name="Male")
    death.gender = [c]

    output = death.model_dump(by_alias=True)
    # Wrapper check
    assert "Death" in output
    inner = output["Death"]
    assert inner["CodesetId"] == 10
    assert inner["Age"]["Value"] == 50
    assert inner["Gender"][0]["CONCEPT_ID"] == 123


def test_death_deserialization_wrapped():
    json_input = """
    {
        "Death": {
            "CodesetId": 99,
            "DeathTypeExclude": false
        }
    }
    """
    obj = TypeAdapter(Criteria).validate_json(json_input)
    assert isinstance(obj, Death)
    assert obj.codeset_id == 99
    assert obj.death_type_exclude is False
