from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    PayerPlanPeriod,
    Criteria,
    ConceptSetSelection,
    NumericRange,
)
from omop_cohort_builder.base import Concept


def test_payer_plan_period_serialization():
    criteria = PayerPlanPeriod(
        first=True,
        payer_concept=123,
        period_length=NumericRange(value=10, op="gt"),
        gender=[Concept(CONCEPT_ID=8507, CONCEPT_NAME="Male")],
        gender_cs=ConceptSetSelection(codeset_id=1),
    )

    # We use exclude_none=True to match OHDSI JSON standard
    json_output = criteria.model_dump(by_alias=True, exclude_none=True)

    expected = {
        "PayerPlanPeriod": {
            "First": True,
            "PayerConcept": 123,
            "PeriodLength": {"Value": 10, "Op": "gt"},
            "Gender": [{"CONCEPT_ID": 8507, "CONCEPT_NAME": "Male"}],
            "GenderCS": {"CodesetId": 1},
        }
    }

    assert json_output == expected


def test_payer_plan_period_deserialization():
    json_input = {
        "PayerPlanPeriod": {
            "First": True,
            "PayerConcept": 123,
            "PeriodLength": {"Value": 10, "Op": "gt"},
            "Gender": [{"CONCEPT_ID": 8507, "CONCEPT_NAME": "Male"}],
            "GenderCS": {"CodesetId": 1},
            "PayerSourceConcept": 456,
        }
    }

    # Use TypeAdapter to validate as the Union type to trigger the deserializer helper
    adapter = TypeAdapter(Criteria)
    criteria = adapter.validate_python(json_input)

    assert isinstance(criteria, PayerPlanPeriod)
    assert criteria.first is True
    assert criteria.payer_concept == 123
    assert criteria.period_length.value == 10
    assert criteria.gender[0].concept_id == 8507
    assert criteria.gender_cs.codeset_id == 1
    assert criteria.payer_source_concept == 456


def test_payer_plan_period_all_fields():
    """Test full coverage of all fields"""
    criteria = PayerPlanPeriod(
        first=False,
        payer_concept=1,
        plan_concept=2,
        sponsor_concept=3,
        stop_reason_concept=4,
        payer_source_concept=5,
        plan_source_concept=6,
        sponsor_source_concept=7,
        stop_reason_source_concept=8,
    )

    dump = criteria.model_dump(by_alias=True, exclude_none=True)
    expected = {
        "PayerPlanPeriod": {
            "First": False,
            "PayerConcept": 1,
            "PlanConcept": 2,
            "SponsorConcept": 3,
            "StopReasonConcept": 4,
            "PayerSourceConcept": 5,
            "PlanSourceConcept": 6,
            "SponsorSourceConcept": 7,
            "StopReasonSourceConcept": 8,
        }
    }
    assert dump == expected
