from omop_cohort_builder.domain import EndStrategy, DateOffset
from pydantic import TypeAdapter


def test_end_strategy_deserializer_with_existing_discriminator():
    # Test the branch where strategy_type is already present in the inner dict
    data = {
        "DateOffset": {
            "strategy_type": "DateOffset",  # Already present
            "DateField": "StartDate",
            "Offset": 10,
        }
    }
    adapter = TypeAdapter(EndStrategy)
    obj = adapter.validate_python(data)
    assert isinstance(obj, DateOffset)
    assert obj.offset == 10
