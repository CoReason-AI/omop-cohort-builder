from omop_cohort_builder.domain import criteria_deserializer, end_strategy_deserializer


def test_criteria_deserializer_coverage():
    # 1. Non-dict input
    assert criteria_deserializer("string") == "string"
    assert criteria_deserializer(123) == 123

    # 2. Dict with len != 1
    assert criteria_deserializer({}) == {}
    assert criteria_deserializer({"A": 1, "B": 2}) == {"A": 1, "B": 2}

    # 3. Dict with len 1 but value not dict
    assert criteria_deserializer({"ConditionOccurrence": 123}) == {
        "ConditionOccurrence": 123
    }

    # 4. Valid structure (injection)
    inp = {"ConditionOccurrence": {"CodesetId": 1}}
    out = criteria_deserializer(inp)
    assert out["criteria_type"] == "ConditionOccurrence"

    # 5. Valid structure with existing discriminator (no overwrite)
    inp2 = {"ConditionOccurrence": {"CodesetId": 1, "criteria_type": "Existing"}}
    out2 = criteria_deserializer(inp2)
    assert out2["criteria_type"] == "Existing"


def test_end_strategy_deserializer_coverage():
    # 1. Non-dict input
    assert end_strategy_deserializer("string") == "string"

    # 2. Dict with len != 1
    assert end_strategy_deserializer({}) == {}

    # 3. Dict with len 1 but value not dict
    assert end_strategy_deserializer({"DateOffset": 123}) == {"DateOffset": 123}

    # 4. Valid structure (injection)
    inp = {"DateOffset": {"DateField": "EndDate"}}
    out = end_strategy_deserializer(inp)
    assert out["strategy_type"] == "DateOffset"
