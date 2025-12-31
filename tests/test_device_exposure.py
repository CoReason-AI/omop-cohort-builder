from omop_cohort_builder.domain import (
    DeviceExposure,
    Criteria,
    ConceptSetSelection,
    TextFilter,
)
from pydantic import TypeAdapter


def test_device_exposure_serialization():
    de = DeviceExposure(
        codeset_id=1,
        first=True,
        device_type_cs=ConceptSetSelection(codeset_id=2),
        device_type_exclude=True,
        unique_device_id=TextFilter(text="123", op="eq"),
        device_source_concept=456,
    )

    # Test wrapper serialization
    dump = de.model_dump(by_alias=True)
    assert "DeviceExposure" in dump
    inner = dump["DeviceExposure"]
    assert inner["CodesetId"] == 1
    assert inner["First"] is True
    assert inner["DeviceTypeCS"]["CodesetId"] == 2
    assert inner["DeviceTypeExclude"] is True
    assert inner["UniqueDeviceId"]["Text"] == "123"
    assert inner["DeviceSourceConcept"] == 456

    # Ensure discriminator is not present in inner dict
    assert "CriteriaType" not in inner
    assert "criteria_type" not in inner


def test_device_exposure_deserialization():
    adapter = TypeAdapter(Criteria)
    data = {
        "DeviceExposure": {
            "CodesetId": 123,
            "First": True,
            "DeviceTypeExclude": True,
            "DeviceSourceConcept": 789,
            "UniqueDeviceId": {"Text": "abc", "Op": "eq"},
        }
    }
    obj = adapter.validate_python(data)
    assert isinstance(obj, DeviceExposure)
    assert obj.codeset_id == 123
    assert obj.first is True
    assert obj.device_type_exclude is True
    assert obj.device_source_concept == 789
    assert obj.unique_device_id.text == "abc"


def test_device_exposure_round_trip():
    adapter = TypeAdapter(Criteria)
    de = DeviceExposure(codeset_id=999, device_source_concept=111)
    dump = de.model_dump(by_alias=True)
    obj = adapter.validate_python(dump)
    assert isinstance(obj, DeviceExposure)
    assert obj.codeset_id == 999
    assert obj.device_source_concept == 111


def test_device_exposure_defaults():
    de = DeviceExposure()
    assert de.device_type_exclude is False
    assert de.codeset_id is None
    dump = de.model_dump(by_alias=True)
    assert dump["DeviceExposure"]["DeviceTypeExclude"] is False
