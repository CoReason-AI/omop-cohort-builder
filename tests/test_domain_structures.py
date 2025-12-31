from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    EndStrategy,
    DateOffset,
    CustomEra,
    CriteriaGroup,
    CorelatedCriteria,
    ConditionOccurrence,
    Occurrence,
    Window,
    DemographicCriteria,
    NumericRange,
)


def test_date_offset_serialization():
    do = DateOffset(date_field="StartDate", offset=7)
    data = do.model_dump(by_alias=True, exclude_none=True)
    assert "DateOffset" in data
    inner = data["DateOffset"]
    assert inner["DateField"] == "StartDate"
    assert inner["Offset"] == 7
    assert "StrategyType" not in inner


def test_date_offset_deserialization():
    json_str = """
    {
        "DateOffset": {
            "DateField": "EndDate",
            "Offset": 10
        }
    }
    """
    adapter = TypeAdapter(EndStrategy)
    obj = adapter.validate_json(json_str)
    assert isinstance(obj, DateOffset)
    assert obj.date_field == "EndDate"
    assert obj.offset == 10


def test_custom_era_serialization():
    ce = CustomEra(drug_codeset_id=123, gap_days=30, offset=5)
    data = ce.model_dump(by_alias=True, exclude_none=True)
    assert "CustomEra" in data
    inner = data["CustomEra"]
    assert inner["DrugCodesetId"] == 123
    assert inner["GapDays"] == 30
    assert inner["Offset"] == 5


def test_custom_era_deserialization():
    json_str = """
    {
        "CustomEra": {
            "DrugCodesetId": 456,
            "GapDays": 10,
            "Offset": 2
        }
    }
    """
    adapter = TypeAdapter(EndStrategy)
    obj = adapter.validate_json(json_str)
    assert isinstance(obj, CustomEra)
    assert obj.drug_codeset_id == 456


def test_criteria_group_serialization():
    cg = CriteriaGroup(
        type="ANY",
        criteria_list=[
            CorelatedCriteria(
                criteria=ConditionOccurrence(codeset_id=1),
                occurrence=Occurrence(type=2, count=1),
                start_window=Window(
                    start=Window.Endpoint(coeff=-1, days=30),
                    end=Window.Endpoint(coeff=1, days=0),
                ),
            )
        ],
        demographic_criteria_list=[
            DemographicCriteria(age=NumericRange(value=18, op="gt"))
        ],
    )

    data = cg.model_dump(by_alias=True, exclude_none=True)
    assert data["Type"] == "ANY"
    assert len(data["CriteriaList"]) == 1
    assert "ConditionOccurrence" in data["CriteriaList"][0]["Criteria"]
    assert len(data["DemographicCriteriaList"]) == 1
    assert data["DemographicCriteriaList"][0]["Age"]["Value"] == 18


def test_criteria_group_is_empty():
    cg = CriteriaGroup()
    assert cg.is_empty() is True

    cg.count = 1
    # is_empty checks lists, not count
    assert cg.is_empty() is True

    cg.criteria_list.append(
        CorelatedCriteria(
            criteria=ConditionOccurrence(codeset_id=1),
            occurrence=Occurrence(type=0, count=0),
            start_window=Window(
                start=Window.Endpoint(coeff=-1), end=Window.Endpoint(coeff=1)
            ),
        )
    )
    assert cg.is_empty() is False


def test_recursive_criteria_group():
    inner_cg = CriteriaGroup(type="ALL", count=1)
    outer_cg = CriteriaGroup(type="ANY", groups=[inner_cg])

    data = outer_cg.model_dump(by_alias=True, exclude_none=True)
    assert len(data["Groups"]) == 1
    assert data["Groups"][0]["Type"] == "ALL"


def test_end_strategy_deserializer_branches():
    # Test cases that might fail strict validation or hit edge cases in deserializer

    # Case 1: Already unwrapped (shouldn't happen with valid JSON input for Union but good for robustness)
    # The deserializer returns v if it's not a dict or len != 1
    from omop_cohort_builder.domain import end_strategy_deserializer

    assert end_strategy_deserializer(123) == 123
    assert end_strategy_deserializer({"A": 1, "B": 2}) == {"A": 1, "B": 2}

    # Case 2: Inner value is not a dict
    assert end_strategy_deserializer({"DateOffset": "Invalid"}) == {
        "DateOffset": "Invalid"
    }

    # Case 3: Already has strategy_type (idempotency)
    inp = {"DateOffset": {"strategy_type": "DateOffset", "Offset": 1}}
    out = end_strategy_deserializer(inp)
    assert out["strategy_type"] == "DateOffset"
