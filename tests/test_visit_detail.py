import json
from pydantic import TypeAdapter
from omop_cohort_builder.domain import (
    VisitDetail,
    Criteria,
    ConceptSetSelection,
    NumericRange,
    DateRange,
)


def test_visit_detail_serialization():
    """Test serialization of VisitDetail to JSON."""
    criteria = VisitDetail(
        codeset_id=1,
        first=True,
        visit_detail_start_date=DateRange(value="2022-01-01", op="gt"),
        visit_detail_end_date=DateRange(value="2022-12-31", op="lt"),
        visit_detail_type_cs=ConceptSetSelection(codeset_id=2, is_exclusion=False),
        visit_detail_source_concept=123,
        visit_detail_length=NumericRange(value=5, op="eq"),
        age=NumericRange(value=30, op="gt"),
        gender_cs=ConceptSetSelection(codeset_id=3, is_exclusion=False),
        provider_specialty_cs=ConceptSetSelection(codeset_id=4, is_exclusion=True),
        place_of_service_cs=ConceptSetSelection(codeset_id=5, is_exclusion=False),
        place_of_service_location=456,
    )

    # Serialize using model_dump_json (which uses aliases by default in V2 if configured)
    # But CirceModel is configured with populate_by_name=True and alias_generator=to_pascal.
    # However, WrappedCriteriaMixin wraps it.

    # FIX: Use exclude_none=True to match OHDSI standard and test expectations
    json_str = criteria.model_dump_json(by_alias=True, exclude_none=True)
    data = json.loads(json_str)

    # Check wrapper
    assert "VisitDetail" in data
    inner = data["VisitDetail"]

    # Check fields
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["VisitDetailStartDate"] == {"Value": "2022-01-01", "Op": "gt"}
    assert inner["VisitDetailEndDate"] == {"Value": "2022-12-31", "Op": "lt"}
    assert inner["VisitDetailTypeCS"] == {"CodesetId": 2, "IsExclusion": False}
    assert inner["VisitDetailSourceConcept"] == 123
    assert inner["VisitDetailLength"] == {"Value": 5, "Op": "eq"}
    assert inner["Age"] == {"Value": 30, "Op": "gt"}
    assert inner["GenderCS"] == {"CodesetId": 3, "IsExclusion": False}
    assert inner["ProviderSpecialtyCS"] == {"CodesetId": 4, "IsExclusion": True}
    assert inner["PlaceOfServiceCS"] == {"CodesetId": 5, "IsExclusion": False}
    assert inner["PlaceOfServiceLocation"] == 456

    # Check excluded fields
    assert "criteria_type" not in inner
    assert "CriteriaType" not in inner


def test_visit_detail_deserialization():
    """Test deserialization of VisitDetail from JSON."""
    json_data = {
        "VisitDetail": {
            "CodesetId": 10,
            "First": False,
            "VisitDetailTypeCS": {"CodesetId": 20},
            "PlaceOfServiceLocation": 789,
        }
    }

    # Use TypeAdapter(Criteria) to test the union deserializer logic
    adapter = TypeAdapter(Criteria)
    obj = adapter.validate_python(json_data)

    assert isinstance(obj, VisitDetail)
    assert obj.codeset_id == 10
    assert obj.first is False
    assert obj.visit_detail_type_cs.codeset_id == 20
    assert obj.place_of_service_location == 789

    # Check unprovided fields are None
    assert obj.visit_detail_start_date is None
    assert obj.gender_cs is None


def test_visit_detail_round_trip():
    """Test full round trip serialization/deserialization."""
    original = VisitDetail(
        codeset_id=99, visit_detail_length=NumericRange(value=10, op="lt")
    )

    json_str = original.model_dump_json(by_alias=True, exclude_none=True)
    adapter = TypeAdapter(Criteria)
    restored = adapter.validate_json(json_str)

    assert isinstance(restored, VisitDetail)
    assert restored.codeset_id == 99
    assert restored.visit_detail_length.value == 10
    assert restored.visit_detail_length.op == "lt"
