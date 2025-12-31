import json
from pathlib import Path

from pydantic import TypeAdapter

from omop_cohort_builder.domain import (
    CohortExpression,
    Criteria,
    ObservationPeriod,
    criteria_deserializer,
    end_strategy_deserializer,
)


def test_observation_period_empty_serialization():
    """
    Test serialization of an empty ObservationPeriod.
    Corresponds to Utils.serialize(new ObservationPeriod()) in Java.
    """
    op = ObservationPeriod()
    # Serialize wrapped in the union adapter to get the type discriminator wrapper
    adapter = TypeAdapter(Criteria)
    # We must exclude_none=True to match Java behavior (Jackson typically skips nulls)
    json_output = adapter.dump_json(op, by_alias=True, exclude_none=True).decode()
    expected = '{"ObservationPeriod":{}}'
    assert json_output == expected


def test_observation_period_parity(snapshot):
    """
    Test deserialization and round-trip serialization using a real Circe JSON resource.
    """
    resource_path = Path(__file__).parent / "resources/observationPeriod_1.json"
    with open(resource_path, "r") as f:
        json_content = f.read()

    # Deserialize
    expression = CohortExpression.model_validate_json(json_content)

    # Verify Structure
    assert expression.primary_criteria is not None
    assert len(expression.primary_criteria.criteria_list) == 1

    criteria_wrapper = expression.primary_criteria.criteria_list[0]
    assert isinstance(criteria_wrapper, ObservationPeriod)
    op = criteria_wrapper

    # Assert Fields
    assert op.first is True
    assert op.period_start_date is not None
    assert op.period_start_date.value == "2014-01-01"

    # Round-trip Serialization
    serialized_json = expression.model_dump_json(by_alias=True, exclude_none=True)

    original_dict = json.loads(json_content)
    serialized_dict = json.loads(serialized_json)

    # Compare CriteriaList specifically
    original_criteria = original_dict["PrimaryCriteria"]["CriteriaList"][0]
    serialized_criteria = serialized_dict["PrimaryCriteria"]["CriteriaList"][0]

    assert original_criteria == serialized_criteria


def test_deserializer_edge_cases():
    """
    Test edge cases for criteria_deserializer and end_strategy_deserializer
    to ensure 100% coverage.
    """
    # 1. Input is not a dict
    assert criteria_deserializer("string") == "string"
    assert end_strategy_deserializer("string") == "string"

    # 2. Input dict has > 1 key
    d_multi = {"A": {}, "B": {}}
    assert criteria_deserializer(d_multi) == d_multi
    assert end_strategy_deserializer(d_multi) == d_multi

    # 3. Input dict value is not a dict (should not happen in valid JSON but possible in loose typing)
    d_bad_val = {"ObservationPeriod": "bad"}
    # The logic: if isinstance(v[key], dict) -> branch taken. Else return v.
    assert criteria_deserializer(d_bad_val) == d_bad_val
    assert end_strategy_deserializer(d_bad_val) == d_bad_val
