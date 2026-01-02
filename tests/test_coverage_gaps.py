from omop_cohort_builder.domain import criteria_deserializer, end_strategy_deserializer
from omop_cohort_builder.builders import QueryBuilder, _get_criteria_columns_dispatch
from omop_cohort_builder.domain import PrimaryCriteria
from sqlalchemy import select
import pytest


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


# --- Query Builder Coverage Tests ---


def test_query_builder_base_not_implemented():
    """
    Test the base build_criteria method raises NotImplementedError
    when called with an unknown criteria type.
    """
    qb = QueryBuilder()

    class UnknownCriteria:
        pass

    with pytest.raises(NotImplementedError) as excinfo:
        qb.build_criteria("not a criteria object")
    assert "Query builder not implemented for type" in str(excinfo.value)


def test_get_criteria_columns_not_implemented():
    """
    Test _get_criteria_columns_dispatch raises NotImplementedError for unknown types.
    Testing the module-level dispatch function directly.
    """
    class UnknownCriteria:
        pass

    with pytest.raises(NotImplementedError) as excinfo:
        _get_criteria_columns_dispatch(UnknownCriteria())
    assert "Column mapping not implemented for type" in str(excinfo.value)


def test_normalize_criteria_query_error():
    """
    Test _normalize_criteria_query raises NotImplementedError when mapping fails.
    """
    qb = QueryBuilder()

    # Use a dummy Select
    query = select(1)

    class UnknownCriteria:
        pass

    with pytest.raises(NotImplementedError) as excinfo:
        qb._normalize_criteria_query(query, UnknownCriteria())
    assert "Cannot normalize query for type" in str(excinfo.value)


def test_build_primary_criteria_empty_list():
    """
    Test build_primary_criteria with empty criteria list returns valid empty select.
    """
    qb = QueryBuilder()
    pc = PrimaryCriteria(
        CriteriaList=[],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "All"},
    )

    query = qb.build_primary_criteria(pc)
    # Check if it selects NULLs and 1!=1
    sql = str(query)
    assert "NULL" in sql
    # exact SQL depends on dialect compilation defaults but should be safe


def test_resolve_codeset_missing():
    """
    Test _resolve_codeset returns empty list for unknown ID.
    """
    qb = QueryBuilder(concept_set_map={1: [100]})
    assert qb._resolve_codeset(2) == []
    assert qb._resolve_codeset(1) == [100]
