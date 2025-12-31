import json
import pytest
from pathlib import Path
from pydantic import TypeAdapter
from omop_cohort_builder.domain import CohortExpression, Criteria

# Define paths to test resources
RESOURCE_ROOT = Path("/tmp/file_attachments/circe-be/src/test/resources")
CRITERIA_DIR = RESOURCE_ROOT / "criteria"
COHORT_GEN_DIR = RESOURCE_ROOT / "cohortgeneration"
PRINT_FRIENDLY_DIR = RESOURCE_ROOT / "printfriendly"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def normalize_json(obj):
    """
    Recursively remove null values and empty lists/dicts if that's the convention,
    BUT strict OHDSI might keep empty lists.
    Java 'include=Include.NON_NULL' usually removes nulls.
    Java arrays often serialize to [] if empty.

    We need to match the Python model_dump(exclude_none=True).
    """
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [normalize_json(item) for item in obj]
    else:
        return obj


def check_parity(model_class, json_path):
    if not json_path.exists():
        pytest.skip(f"File not found: {json_path}")

    original_json = load_json(json_path)

    # Parse
    try:
        if model_class is Criteria:
            adapter = TypeAdapter(Criteria)
            model = adapter.validate_python(original_json)
        else:
            model = model_class.model_validate(original_json)
    except Exception as e:
        pytest.fail(f"Failed to parse {json_path}: {e}")

    # Dump
    dumped_json = model.model_dump(by_alias=True, exclude_none=True)

    # Normalize original (remove nulls) to match dumped
    original_normalized = normalize_json(original_json)

    # Helper to diff if assert fails
    if original_normalized != dumped_json:
        import pprint

        print(f"\nDiff for {json_path.name}:")
        print("Original (Normalized):")
        pprint.pprint(original_normalized)
        print("Dumped:")
        pprint.pprint(dumped_json)

    assert dumped_json == original_normalized


@pytest.mark.parametrize(
    "filename",
    [
        "conditionOccurrence.json",
        "drugExposure.json",
        "visit.json",  # added visit
        "death.json",  # added death
    ],
)
def test_printfriendly_parity(filename):
    # These are CohortExpression objects
    check_parity(CohortExpression, PRINT_FRIENDLY_DIR / filename)


@pytest.mark.parametrize("filename", ["simpleInclusionRule.json"])
def test_cohort_inclusion_rules(filename):
    check_parity(CohortExpression, COHORT_GEN_DIR / "inclusionRules" / filename)


@pytest.mark.parametrize("filename", ["limitExpression.json"])
def test_cohort_limits(filename):
    check_parity(CohortExpression, COHORT_GEN_DIR / "limits" / filename)


def test_concept_set_parity():
    # Test a concept set expression if available
    # But ConceptSet in JSON is part of CohortExpression.
    # We can test mixedConceptsets
    check_parity(
        CohortExpression,
        COHORT_GEN_DIR / "mixedConceptsets" / "mixedConceptsetsExpression.json",
    )
