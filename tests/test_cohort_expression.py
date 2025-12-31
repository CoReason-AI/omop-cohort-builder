from omop_cohort_builder.domain import CohortExpression, ResultLimit
import json

# Minimal valid Cohort Expression JSON (derived from printfriendly/conditionOccurrence.json)
SIMPLE_COHORT_JSON = """
{
  "ConceptSets": [],
  "PrimaryCriteria": {
    "CriteriaList": [
      {
        "ConditionOccurrence": {
          "CodesetId": 0
        }
      }
    ],
    "ObservationWindow": {
      "PriorDays": 0,
      "PostDays": 0
    },
    "PrimaryCriteriaLimit": {
      "Type": "First"
    }
  },
  "QualifiedLimit": {
    "Type": "First"
  },
  "ExpressionLimit": {
    "Type": "First"
  },
  "InclusionRules": [],
  "CensoringCriteria": [],
  "CollapseSettings": {
    "CollapseType": "ERA",
    "EraPad": 0
  },
  "CensorWindow": {},
  "cdmVersionRange": ">=5.0.0",
  "Title": "Test Title"
}
"""


def test_cohort_expression_deserialization():
    cohort = CohortExpression.model_validate_json(SIMPLE_COHORT_JSON)

    assert cohort.cdm_version_range == ">=5.0.0"
    assert cohort.title == "Test Title"
    assert len(cohort.concept_sets) == 0
    assert len(cohort.primary_criteria.criteria_list) == 1
    assert cohort.collapse_settings.collapse_type == "ERA"


def test_result_limit_structure():
    limit = ResultLimit(type="Last")
    assert limit.type == "Last"
    dump = limit.model_dump(by_alias=True)
    assert dump["Type"] == "Last"


def test_cohort_expression_serialization():
    # Load -> Dump -> Load -> Compare
    cohort = CohortExpression.model_validate_json(SIMPLE_COHORT_JSON)
    dump_json = cohort.model_dump_json(by_alias=True, exclude_none=True)

    data = json.loads(dump_json)

    # Verify Top Level Keys (PascalCase usually)
    assert "ConceptSets" in data
    assert "PrimaryCriteria" in data
    assert "InclusionRules" in data
    assert "CollapseSettings" in data
    assert "CensorWindow" in data
    # Exception: cdmVersionRange (mixed)
    assert "cdmVersionRange" in data
    assert data["cdmVersionRange"] == ">=5.0.0"
    assert "Title" in data
    assert data["Title"] == "Test Title"


def test_cohort_expression_with_concept_sets():
    # Test that list of ConceptSet (camelCase) works inside CohortExpression (PascalCase)
    json_input = """
    {
      "ConceptSets": [
        {
          "id": 1,
          "name": "Test Set",
          "expression": {"items": []}
        }
      ],
      "PrimaryCriteria": {
        "CriteriaList": [],
        "ObservationWindow": {"PriorDays": 0, "PostDays": 0},
        "PrimaryCriteriaLimit": {"Type": "All"}
      },
      "QualifiedLimit": {"Type": "All"},
      "ExpressionLimit": {"Type": "All"},
      "CollapseSettings": {"CollapseType": "ERA", "EraPad": 0},
      "CensorWindow": {}
    }
    """
    cohort = CohortExpression.model_validate_json(json_input)
    assert len(cohort.concept_sets) == 1
    cs = cohort.concept_sets[0]
    assert cs.id == 1
    assert cs.name == "Test Set"

    # Serialize back
    dump = cohort.model_dump(by_alias=True)
    assert "ConceptSets" in dump
    cs_dump = dump["ConceptSets"][0]
    assert "id" in cs_dump  # CamelCaseModel should output "id"
    assert "name" in cs_dump
    assert cs_dump["name"] == "Test Set"
