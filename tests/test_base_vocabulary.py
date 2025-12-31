from omop_cohort_builder.base import (
    Concept,
    ConceptSetSelection,
    DateAdjustment,
)


def test_concept_serialization():
    c = Concept(
        concept_id=123,
        concept_name="Test Concept",
        standard_concept="S",
        invalid_reason=None,
        concept_code="A01",
        domain_id="Drug",
        vocabulary_id="RxNorm",
        concept_class_id="Ingredient",
    )
    dumped = c.model_dump(by_alias=True, exclude_none=True)
    expected = {
        "CONCEPT_ID": 123,
        "CONCEPT_NAME": "Test Concept",
        "STANDARD_CONCEPT": "S",
        "CONCEPT_CODE": "A01",
        "DOMAIN_ID": "Drug",
        "VOCABULARY_ID": "RxNorm",
        "CONCEPT_CLASS_ID": "Ingredient",
    }
    assert dumped == expected


def test_concept_deserialization():
    data = {
        "CONCEPT_ID": 456,
        "CONCEPT_NAME": "Another Concept",
        "STANDARD_CONCEPT": None,
        "INVALID_REASON": "D",
        "CONCEPT_CODE": "B02",
        "DOMAIN_ID": "Condition",
        "VOCABULARY_ID": "SNOMED",
        "CONCEPT_CLASS_ID": "Clinical Finding",
    }
    c = Concept.model_validate(data)
    assert c.concept_id == 456
    assert c.invalid_reason == "D"
    assert c.standard_concept is None


def test_concept_set_selection_serialization():
    css = ConceptSetSelection(codeset_id=1)
    dumped = css.model_dump(by_alias=True)
    assert dumped == {"CodesetId": 1, "IsExclusion": None}

    css_ex = ConceptSetSelection(codeset_id=2, is_exclusion=True)
    dumped_ex = css_ex.model_dump(by_alias=True)
    assert dumped_ex == {"CodesetId": 2, "IsExclusion": True}


def test_date_adjustment_serialization():
    da = DateAdjustment(
        start_with=DateAdjustment.DateType.END_DATE,
        start_offset=7,
        end_with=DateAdjustment.DateType.START_DATE,
        end_offset=-7,
    )
    dumped = da.model_dump(by_alias=True)
    assert dumped == {
        "StartWith": "END_DATE",
        "StartOffset": 7,
        "EndWith": "START_DATE",
        "EndOffset": -7,
    }


def test_date_adjustment_defaults():
    da = DateAdjustment()
    dumped = da.model_dump(by_alias=True)
    assert dumped == {
        "StartWith": "START_DATE",
        "StartOffset": 0,
        "EndWith": "END_DATE",
        "EndOffset": 0,
    }
