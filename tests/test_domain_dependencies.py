from omop_cohort_builder.domain import (
    CollapseSettings,
    CensorWindow,
    DateOffset,
    CustomEra,
    EndStrategy,
    InclusionRule,
    CriteriaGroup,
)
from pydantic import TypeAdapter
import json


def test_collapse_settings_serialization():
    cs = CollapseSettings(collapse_type="ERA", era_pad=0)
    dump = cs.model_dump(by_alias=True)
    assert dump["CollapseType"] == "ERA"
    assert dump["EraPad"] == 0


def test_censor_window_serialization():
    cw = CensorWindow(start_date="2000-04-01", end_date="2000-09-01")
    dump = cw.model_dump(by_alias=True)
    assert dump["StartDate"] == "2000-04-01"
    assert dump["EndDate"] == "2000-09-01"

    cw_empty = CensorWindow()
    dump_empty = cw_empty.model_dump(by_alias=True, exclude_none=True)
    assert dump_empty == {}


def test_date_offset_serialization():
    # Polymorphic test
    strategy = DateOffset(date_field="StartDate", offset=90)

    # Direct dump (WrappedStrategyMixin should wrap it)
    dump = strategy.model_dump_json(by_alias=True)
    data = json.loads(dump)

    assert "DateOffset" in data
    inner = data["DateOffset"]
    assert inner["DateField"] == "StartDate"
    assert inner["Offset"] == 90
    assert "StrategyType" not in inner


def test_custom_era_serialization():
    strategy = CustomEra(
        drug_codeset_id=10, gap_days=14, offset=1, days_supply_override=7
    )
    dump = strategy.model_dump_json(by_alias=True)
    data = json.loads(dump)

    assert "CustomEra" in data
    inner = data["CustomEra"]
    assert inner["DrugCodesetId"] == 10
    assert inner["GapDays"] == 14
    assert inner["Offset"] == 1
    assert inner["DaysSupplyOverride"] == 7


def test_end_strategy_polymorphism():
    adapter = TypeAdapter(EndStrategy)

    # Test DateOffset
    json_do = '{"DateOffset": {"DateField": "EndDate", "Offset": 7}}'
    obj_do = adapter.validate_json(json_do)
    assert isinstance(obj_do, DateOffset)
    assert obj_do.date_field == "EndDate"
    assert obj_do.offset == 7

    # Test CustomEra
    json_ce = '{"CustomEra": {"DrugCodesetId": 0, "GapDays": 14, "Offset": 1}}'
    obj_ce = adapter.validate_json(json_ce)
    assert isinstance(obj_ce, CustomEra)
    assert obj_ce.drug_codeset_id == 0
    assert obj_ce.gap_days == 14


def test_inclusion_rule_serialization():
    # InclusionRule uses CirceCamelModel (camelCase)
    # expression is CriteriaGroup (PascalCase)

    group = CriteriaGroup(type="ALL", count=1)
    rule = InclusionRule(name="Rule 1", description="Desc", expression=group)

    dump = rule.model_dump(by_alias=True)

    # Check camelCase keys
    assert "name" in dump
    assert dump["name"] == "Rule 1"
    assert "description" in dump
    assert dump["description"] == "Desc"
    assert "expression" in dump

    # Check inner CriteriaGroup (PascalCase)
    expr = dump["expression"]
    assert "Type" in expr
    assert expr["Type"] == "ALL"
    assert "Count" in expr
    assert expr["Count"] == 1


def test_end_strategy_deserializer_coverage():
    from omop_cohort_builder.domain import end_strategy_deserializer

    assert end_strategy_deserializer("foo") == "foo"
    assert end_strategy_deserializer({"A": 1, "B": 2}) == {"A": 1, "B": 2}

    # Test valid dict structure but inner value not dict (missing branch 250)
    assert end_strategy_deserializer({"A": 1}) == {"A": 1}


def test_strategy_serialization_by_alias_false():
    # Cover missing lines in WrappedStrategyMixin
    # 225: if "StrategyType" in data
    # 227: if "strategy_type" in data

    # Case 1: by_alias=False (snake_case), "strategy_type" is present
    strategy = DateOffset(date_field="d", offset=1)
    dump = strategy.model_dump(by_alias=False)
    assert "DateOffset" in dump
    inner = dump["DateOffset"]
    assert "strategy_type" not in inner
    assert "StrategyType" not in inner
    assert "date_field" in inner
