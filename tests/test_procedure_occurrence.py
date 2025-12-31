from omop_cohort_builder.domain import (
    ProcedureOccurrence,
    Criteria,
    ConceptSetSelection,
    Concept,
    NumericRange,
)
from pydantic import TypeAdapter


def test_procedure_occurrence_serialization():
    po = ProcedureOccurrence(
        codeset_id=200,
        first=False,
        procedure_type_exclude=True,
        procedure_type_cs=ConceptSetSelection(codeset_id=201),
        quantity=NumericRange(value=5, op="gt"),
    )

    dump = po.model_dump(by_alias=True)
    assert "ProcedureOccurrence" in dump
    inner = dump["ProcedureOccurrence"]
    assert inner["CodesetId"] == 200
    assert inner["First"] is False
    assert inner["ProcedureTypeExclude"] is True
    assert inner["ProcedureTypeCS"]["CodesetId"] == 201
    assert inner["Quantity"]["Value"] == 5
    assert inner["Quantity"]["Op"] == "gt"


def test_procedure_occurrence_polymorphism():
    adapter = TypeAdapter(Criteria)
    data = {
        "ProcedureOccurrence": {
            "CodesetId": 300,
            "ProcedureSourceConcept": 444,
            "ModifierCS": {"CodesetId": 555},
        }
    }
    obj = adapter.validate_python(data)
    assert isinstance(obj, ProcedureOccurrence)
    assert obj.codeset_id == 300
    assert obj.procedure_source_concept == 444
    assert obj.modifier_cs.codeset_id == 555


def test_procedure_occurrence_round_trip():
    adapter = TypeAdapter(Criteria)
    po = ProcedureOccurrence(
        codeset_id=10,
        gender=[Concept(CONCEPT_ID=1, CONCEPT_NAME="Male")],
        visit_type_cs=ConceptSetSelection(codeset_id=99),
    )
    dump = po.model_dump(by_alias=True)
    obj = adapter.validate_python(dump)
    assert isinstance(obj, ProcedureOccurrence)
    assert obj.codeset_id == 10
    assert obj.gender[0].concept_id == 1
    assert obj.visit_type_cs.codeset_id == 99
