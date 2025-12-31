from omop_cohort_builder.domain import LocationRegion, Criteria, DateRange
from pydantic import TypeAdapter


def test_location_region_serialization():
    # Test snake_case -> PascalCase serialization
    lr = LocationRegion(
        codeset_id=123,
        start_date=DateRange(value="2020-01-01", op="gt"),
        end_date=DateRange(value="2021-01-01", op="lt"),
    )

    dump = lr.model_dump(by_alias=True, exclude_none=True)

    assert dump["LocationRegion"]["CodesetId"] == 123
    assert dump["LocationRegion"]["StartDate"]["Value"] == "2020-01-01"
    assert dump["LocationRegion"]["StartDate"]["Op"] == "gt"
    assert dump["LocationRegion"]["EndDate"]["Value"] == "2021-01-01"
    assert dump["LocationRegion"]["EndDate"]["Op"] == "lt"


def test_location_region_deserialization():
    # Test PascalCase -> snake_case deserialization
    data = {
        "LocationRegion": {
            "CodesetId": 456,
            "StartDate": {"Value": "2022-01-01", "Op": "eq"},
        }
    }

    # Use TypeAdapter for polymorphic deserialization
    adapter = TypeAdapter(Criteria)
    model = adapter.validate_python(data)

    assert isinstance(model, LocationRegion)
    assert model.codeset_id == 456
    assert model.start_date.value == "2022-01-01"
    assert model.start_date.op == "eq"
    assert model.end_date is None


def test_location_region_direct_deserialization():
    # Test direct deserialization without wrapper
    data = {"CodesetId": 789, "StartDate": {"Value": "2023-01-01", "Op": "lte"}}

    model = LocationRegion.model_validate(data)
    assert model.codeset_id == 789
    assert model.start_date.value == "2023-01-01"
    assert model.start_date.op == "lte"
