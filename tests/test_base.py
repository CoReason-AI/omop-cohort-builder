from omop_cohort_builder.base import to_pascal, CirceModel


def test_to_pascal():
    assert to_pascal("snake_case") == "SnakeCase"
    assert to_pascal("simple") == "Simple"
    assert to_pascal("multi_word_string") == "MultiWordString"
    # Note: CS suffix handling is done via manual alias in domain models,
    # so to_pascal defaults to Cs.
    assert to_pascal("some_cs") == "SomeCs"


class ExampleModel(CirceModel):
    some_field: str
    another_field: int


def test_circe_model_serialization():
    model = ExampleModel(some_field="value", another_field=123)
    dump = model.model_dump(by_alias=True)
    assert dump["SomeField"] == "value"
    assert dump["AnotherField"] == 123


def test_circe_model_deserialization():
    data = {"SomeField": "value", "AnotherField": 123}
    model = ExampleModel.model_validate(data)
    assert model.some_field == "value"
    assert model.another_field == 123
