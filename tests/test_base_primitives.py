from omop_cohort_builder.base import (
    CirceModel,
    TextFilter,
    NumericRange,
    DateRange,
    Period,
)


def test_circe_model_pascal_case_alias():
    class TestModel(CirceModel):
        some_field: str
        another_field: int

    model = TestModel(some_field="test", another_field=123)
    dumped = model.model_dump(by_alias=True)
    assert dumped["SomeField"] == "test"
    assert dumped["AnotherField"] == 123
    assert "some_field" not in dumped


def test_text_filter_serialization():
    tf = TextFilter(text="foo", op="eq")
    dumped = tf.model_dump(by_alias=True)
    assert dumped == {"Text": "foo", "Op": "eq"}


def test_text_filter_deserialization():
    data = {"Text": "bar", "Op": "!eq"}
    tf = TextFilter.model_validate(data)
    assert tf.text == "bar"
    assert tf.op == "!eq"


def test_numeric_range_serialization():
    nr = NumericRange(value=10, op="gt", extent=20)
    dumped = nr.model_dump(by_alias=True)
    assert dumped == {"Value": 10, "Op": "gt", "Extent": 20}

    # Test optional extent
    nr_no_extent = NumericRange(value=5, op="lt")
    dumped_ne = nr_no_extent.model_dump(by_alias=True, exclude_none=True)
    assert dumped_ne == {"Value": 5, "Op": "lt"}


def test_numeric_range_types():
    # Verify int is accepted
    nr = NumericRange(value=100, op="eq")
    assert isinstance(nr.value, int)

    # Verify float is accepted
    nr_float = NumericRange(value=10.5, op="eq")
    assert isinstance(nr_float.value, float)


def test_date_range_serialization():
    dr = DateRange(value="2023-01-01", op="eq", extent="2023-12-31")
    dumped = dr.model_dump(by_alias=True)
    assert dumped == {"Value": "2023-01-01", "Op": "eq", "Extent": "2023-12-31"}


def test_period_serialization():
    p = Period(start_date="2023-01-01", end_date="2024-01-01")
    dumped = p.model_dump(by_alias=True)
    assert dumped == {"StartDate": "2023-01-01", "EndDate": "2024-01-01"}
