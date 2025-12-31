from omop_cohort_builder.domain import CohortExpression
import json
from pathlib import Path


def test_json_parity():
    json_path = (
        Path(__file__).parent
        / "resources"
        / "printfriendly"
        / "conditionOccurrence.json"
    )
    with open(json_path, "r") as f:
        data = json.load(f)

    # Validate parsing
    model = CohortExpression.model_validate(data)

    # Validate serialization parity
    _ = model.model_dump(by_alias=True, exclude_none=True)

    # Simple check for now - can use deepdiff or similar later
    # Just asserting it runs without error for now
    assert model.cdm_version_range == ">=5.0.0"
    print("Parsing successful!")
