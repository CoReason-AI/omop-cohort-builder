from omop_cohort_builder.domain import ConditionOccurrence, DrugExposure
from omop_cohort_builder.base import (
    TextFilter,
    NumericRange,
    DateRange,
    Concept,
    ConceptSetSelection,
)
import json


def test_condition_occurrence_serialization():
    co = ConditionOccurrence(
        codeset_id=1,
        first=True,
        occurrence_start_date=DateRange(value="2023-01-01", op="gt"),
        age=NumericRange(value=18, op="gt"),
        gender=[
            Concept(
                concept_id=8507,
                concept_name="Male",
                concept_code="M",
                domain_id="Gender",
                vocabulary_id="Gender",
                concept_class_id="Gender",
            )
        ],
        gender_cs=ConceptSetSelection(codeset_id=2),
    )
    # The new architecture wraps output automatically
    dumped_json = co.model_dump_json(by_alias=True)
    dumped = json.loads(dumped_json)

    assert "ConditionOccurrence" in dumped
    inner = dumped["ConditionOccurrence"]

    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["OccurrenceStartDate"]["Value"] == "2023-01-01"
    assert inner["Age"]["Value"] == 18
    assert inner["Gender"][0]["CONCEPT_ID"] == 8507
    assert inner["GenderCS"]["CodesetId"] == 2


def test_drug_exposure_serialization():
    de = DrugExposure(
        codeset_id=10,
        drug_type_exclude=True,
        refills=NumericRange(value=1, op="gt"),
        stop_reason=TextFilter(text="side effect", op="eq"),
    )
    dumped_json = de.model_dump_json(by_alias=True)
    dumped = json.loads(dumped_json)

    assert "DrugExposure" in dumped
    inner = dumped["DrugExposure"]

    assert inner["CodesetId"] == 10
    assert inner["DrugTypeExclude"] is True
    assert inner["Refills"]["Value"] == 1
    assert inner["StopReason"]["Text"] == "side effect"


def test_custom_aliases_cs_suffix():
    # Verify that fields ending in _cs are serialized to ...CS, not ...Cs
    co = ConditionOccurrence(condition_type_cs=ConceptSetSelection(codeset_id=99))
    dumped = json.loads(co.model_dump_json(by_alias=True))
    inner = dumped["ConditionOccurrence"]
    assert "ConditionTypeCS" in inner
    assert "ConditionTypeCs" not in inner

    de = DrugExposure(route_concept_cs=ConceptSetSelection(codeset_id=88))
    dumped_de = json.loads(de.model_dump_json(by_alias=True))
    inner_de = dumped_de["DrugExposure"]
    assert "RouteConceptCS" in inner_de
