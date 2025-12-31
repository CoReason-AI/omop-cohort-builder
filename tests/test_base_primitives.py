from omop_cohort_builder.base import (
    TextFilter,
    NumericRange,
    DateRange,
    Period,
    Concept,
    ConceptSetSelection,
    DateAdjustment,
    Occurrence,
    CriteriaColumn,
)


def test_text_filter_serialization():
    # Java: @JsonProperty("Text") public String text; @JsonProperty("Op") public String op;
    tf = TextFilter(text="diabetes", op="contains")
    expected = {"Text": "diabetes", "Op": "contains"}
    assert tf.model_dump(by_alias=True) == expected


def test_numeric_range_serialization():
    # Java: @JsonProperty("Value") public Number value; @JsonProperty("Op") public String op; @JsonProperty("Extent") public Number extent;
    nr = NumericRange(value=5, op="gt")
    assert nr.model_dump(by_alias=True, exclude_none=True) == {"Value": 5, "Op": "gt"}


def test_date_range_serialization():
    # Java: @JsonProperty("Value") String value; @JsonProperty("Op") String op; @JsonProperty("Extent") String extent;
    dr = DateRange(value="2023-01-01", op="eq")
    assert dr.model_dump(by_alias=True, exclude_none=True) == {
        "Value": "2023-01-01",
        "Op": "eq",
    }


def test_period_serialization():
    # Java: @JsonProperty("StartDate") String startDate; @JsonProperty("EndDate") String endDate;
    p = Period(start_date="2023-01-01", end_date="2023-12-31")
    assert p.model_dump(by_alias=True) == {
        "StartDate": "2023-01-01",
        "EndDate": "2023-12-31",
    }


def test_concept_serialization():
    # Java: @JsonProperty("CONCEPT_ID") Long conceptId; ...
    c = Concept(
        concept_id=123,
        concept_name="Test Concept",
        standard_concept="S",
        standard_concept_caption="Standard",
        invalid_reason="V",
        invalid_reason_caption="Valid",
        concept_code="ABC",
        domain_id="Condition",
        vocabulary_id="SNOMED",
        concept_class_id="Clinical Finding",
    )
    expected = {
        "CONCEPT_ID": 123,
        "CONCEPT_NAME": "Test Concept",
        "STANDARD_CONCEPT": "S",
        "STANDARD_CONCEPT_CAPTION": "Standard",
        "INVALID_REASON": "V",
        "INVALID_REASON_CAPTION": "Valid",
        "CONCEPT_CODE": "ABC",
        "DOMAIN_ID": "Condition",
        "VOCABULARY_ID": "SNOMED",
        "CONCEPT_CLASS_ID": "Clinical Finding",
    }
    assert c.model_dump(by_alias=True) == expected


def test_concept_set_selection_serialization():
    # Java: @JsonProperty("CodesetId") Integer codesetId; @JsonProperty("IsExclusion") boolean isExclusion;
    # Note: PascalCase
    css = ConceptSetSelection(codeset_id=1, is_exclusion=True)
    expected = {"CodesetId": 1, "IsExclusion": True}
    assert css.model_dump(by_alias=True) == expected


def test_date_adjustment_serialization():
    # Java: @JsonProperty("StartWith") DateType startWith; ...
    # Enum: @JsonProperty("START_DATE") START_DATE
    da = DateAdjustment(
        start_with=DateAdjustment.DateType.START_DATE,
        start_offset=0,
        end_with=DateAdjustment.DateType.END_DATE,
        end_offset=7,
    )
    expected = {
        "StartWith": "START_DATE",
        "StartOffset": 0,
        "EndWith": "END_DATE",
        "EndOffset": 7,
    }
    assert da.model_dump(by_alias=True) == expected


def test_occurrence_serialization():
    # Java: @JsonProperty("Type") int type; @JsonProperty("Count") int count; ...
    occ = Occurrence(
        type=Occurrence.AT_LEAST,
        count=1,
        is_distinct=True,
        count_column=CriteriaColumn.START_DATE,
    )
    expected = {
        "Type": 2,
        "Count": 1,
        "IsDistinct": True,
        "CountColumn": "start_date",  # Enum value
    }
    assert occ.model_dump(by_alias=True) == expected


def test_to_camel_utility():
    from omop_cohort_builder.base import to_camel

    assert to_camel("snake_case_string") == "snakeCaseString"
    assert to_camel("simple") == "simple"
