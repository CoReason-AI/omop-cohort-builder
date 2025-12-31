import json
import hashlib
import difflib
from pathlib import Path
from omop_cohort_builder.domain import CohortExpression


def test_cohort_expression_parity():
    """
    Validates that deserializing and then serializing the reference JSON
    results in an identical JSON structure (parity check).
    """
    # Locate the test resource
    json_path = (
        Path(__file__).parent
        / "resources"
        / "printfriendly"
        / "conditionOccurrence.json"
    )
    if not json_path.exists():
        # Fallback for running from root
        json_path = Path("tests/resources/printfriendly/conditionOccurrence.json")

    assert json_path.exists(), f"Could not find test resource at {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        original_data = json.load(f)

    # 1. Deserialize
    model = CohortExpression.model_validate(original_data)

    # 2. Serialize
    # by_alias=True: Use PascalCase/camelCase aliases
    # exclude_none=True: OHDSI JSON omits nulls
    serialized_data = model.model_dump(by_alias=True, exclude_none=True)

    # 3. Canonicalize (Sort keys for stable comparison)
    orig_str = json.dumps(original_data, sort_keys=True, indent=2)
    new_str = json.dumps(serialized_data, sort_keys=True, indent=2)

    # 4. Compare
    if orig_str != new_str:
        diff = difflib.unified_diff(
            orig_str.splitlines(),
            new_str.splitlines(),
            fromfile="original.json",
            tofile="serialized.json",
            lineterm="",
        )
        diff_text = "\n".join(diff)
        print(f"Serialization Discrepancy Found:\n{diff_text}")

        # Fail the test if they don't match
        assert orig_str == new_str, "Serialized JSON does not match original JSON"

    # 5. MD5 Hash Check (Strict Parity)
    orig_md5 = hashlib.md5(orig_str.encode("utf-8")).hexdigest()
    new_md5 = hashlib.md5(new_str.encode("utf-8")).hexdigest()

    assert orig_md5 == new_md5, f"MD5 mismatch: Original={orig_md5}, New={new_md5}"
