from omop_cohort_builder.domain import (
    ConceptSet,
    ConceptSetExpression,
    ConceptSetItem,
    Concept,
)
import json


def test_concept_set_serialization():
    # Arrange
    item = ConceptSetItem(
        concept=Concept(
            concept_id=140168,
            concept_name="Psoriasis",
            standard_concept="S",
            standard_concept_caption="Standard",
            invalid_reason="V",
            invalid_reason_caption="Valid",
            concept_code="9014002",
            domain_id="Condition",
            vocabulary_id="SNOMED",
            concept_class_id="Clinical Finding",
        ),
        include_descendants=True,
    )

    expression = ConceptSetExpression(items=[item])

    concept_set = ConceptSet(id=1, name="Only Descendants", expression=expression)

    # Act
    # Using by_alias=True to trigger the CamelCase alias generator
    json_output = concept_set.model_dump_json(by_alias=True)
    data = json.loads(json_output)

    # Assert
    assert data["id"] == 1
    assert data["name"] == "Only Descendants"

    # Check expression structure
    assert "expression" in data
    assert "items" in data["expression"]
    assert len(data["expression"]["items"]) == 1

    # Check item fields (Should be camelCase)
    item_json = data["expression"]["items"][0]
    assert "includeDescendants" in item_json
    assert item_json["includeDescendants"] is True
    assert "isExcluded" in item_json
    assert item_json["isExcluded"] is False  # Default
    assert "includeMapped" in item_json
    assert item_json["includeMapped"] is False  # Default

    # Check concept fields (Should be UPPERCASE as per Concept definition)
    assert "concept" in item_json
    concept_json = item_json["concept"]
    assert concept_json["CONCEPT_ID"] == 140168
    assert concept_json["CONCEPT_NAME"] == "Psoriasis"


def test_concept_set_deserialization():
    json_input = """
    {
      "id": 1,
      "name": "Only Descendants",
      "expression": {
        "items": [
          {
            "concept": {
              "CONCEPT_ID": 140168,
              "CONCEPT_NAME": "Psoriasis",
              "STANDARD_CONCEPT": "S",
              "STANDARD_CONCEPT_CAPTION": "Standard",
              "INVALID_REASON": "V",
              "INVALID_REASON_CAPTION": "Valid",
              "CONCEPT_CODE": "9014002",
              "DOMAIN_ID": "Condition",
              "VOCABULARY_ID": "SNOMED",
              "CONCEPT_CLASS_ID": "Clinical Finding"
            },
            "includeDescendants": true,
            "isExcluded": false
          }
        ]
      }
    }
    """

    # Act
    concept_set = ConceptSet.model_validate_json(json_input)

    # Assert
    assert concept_set.id == 1
    assert concept_set.name == "Only Descendants"
    assert len(concept_set.expression.items) == 1

    item = concept_set.expression.items[0]
    assert item.include_descendants is True
    assert item.is_excluded is False
    assert item.concept.concept_id == 140168
    assert item.concept.concept_name == "Psoriasis"
