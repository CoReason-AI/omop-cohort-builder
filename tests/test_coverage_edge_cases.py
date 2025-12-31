from omop_cohort_builder.domain import (
    criteria_deserializer,
    end_strategy_deserializer,
    ConditionOccurrence,
    DateOffset,
    CriteriaGroup,
)


def test_criteria_deserializer_coverage():
    # 1. Not a dict
    assert criteria_deserializer(123) == 123

    # 2. Dict but not len 1
    assert criteria_deserializer({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    # 3. Dict len 1, but value not dict
    assert criteria_deserializer({"Type": 123}) == {"Type": 123}

    # 4. Valid wrapper
    res = criteria_deserializer({"ConditionOccurrence": {"codesetId": 1}})
    assert res["criteria_type"] == "ConditionOccurrence"
    assert res["codesetId"] == 1

    # 5. Already has criteria_type (should happen rarely but handled)
    res = criteria_deserializer(
        {"ConditionOccurrence": {"criteria_type": "Other", "val": 1}}
    )
    assert res["criteria_type"] == "Other"


def test_end_strategy_deserializer_coverage():
    # 1. Not a dict
    assert end_strategy_deserializer(123) == 123

    # 2. Dict but not len 1
    assert end_strategy_deserializer({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    # 3. Dict len 1, but value not dict
    assert end_strategy_deserializer({"Type": 123}) == {"Type": 123}

    # 4. Valid wrapper
    res = end_strategy_deserializer({"DateOffset": {"offset": 1}})
    assert res["strategy_type"] == "DateOffset"
    assert res["offset"] == 1

    # 5. Already has strategy_type
    res = end_strategy_deserializer(
        {"DateOffset": {"strategy_type": "Other", "offset": 1}}
    )
    assert res["strategy_type"] == "Other"


def test_wrapper_serialization_coverage():
    # Test ConditionOccurrence serialization (WrappedCriteriaMixin)
    co = ConditionOccurrence(codeset_id=123)
    dumped = co.model_dump(by_alias=True, exclude_none=True)
    assert "ConditionOccurrence" in dumped
    assert dumped["ConditionOccurrence"]["CodesetId"] == 123

    # Test DateOffset serialization (WrappedStrategyMixin)
    do = DateOffset(offset=5)
    dumped_do = do.model_dump(by_alias=True, exclude_none=True)
    assert "DateOffset" in dumped_do
    assert dumped_do["DateOffset"]["Offset"] == 5


def test_criteria_group_is_empty():
    cg = CriteriaGroup()
    assert cg.is_empty() is True

    # Not empty
    cg.count = 1
    # is_empty checks lists
    assert cg.is_empty() is True

    cg.criteria_list.append("dummy")
    assert cg.is_empty() is False
