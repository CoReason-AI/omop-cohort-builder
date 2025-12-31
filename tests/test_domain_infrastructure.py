from omop_cohort_builder.base import Occurrence, CriteriaColumn
from omop_cohort_builder.domain import Window, CriteriaGroup, DemographicCriteria

# We need to mock 'Criteria' or ensure it resolves to something for testing
# since we haven't implemented the concrete Criteria/Union yet.
# For now, we can test the structure without instantiating the 'criteria' field
# or by using a mock if Pydantic allows.
# Actually, since 'Criteria' is a ForwardRef that isn't fully resolved to a class in domain.py,
# instantiating WindowedCriteria might fail validation if we try to assign something.
# But let's try to test the other parts.


def test_occurrence_serialization():
    occ = Occurrence(
        type=Occurrence.AT_LEAST,
        count=1,
        is_distinct=True,
        count_column=CriteriaColumn.START_DATE,
    )
    dumped = occ.model_dump(by_alias=True)
    assert dumped == {
        "Type": 2,
        "Count": 1,
        "IsDistinct": True,
        "CountColumn": "start_date",
    }


def test_window_serialization():
    w = Window(
        start=Window.Endpoint(days=-30, coeff=-1),
        end=Window.Endpoint(days=0, coeff=1),
        use_index_end=True,
    )
    dumped = w.model_dump(by_alias=True, exclude_none=True)
    assert dumped == {
        "Start": {"Days": -30, "Coeff": -1},
        "End": {"Days": 0, "Coeff": 1},
        "UseIndexEnd": True,
    }


def test_criteria_group_recursion():
    # Test that CriteriaGroup can contain other CriteriaGroups
    inner_group = CriteriaGroup(type="ANY", count=1)
    outer_group = CriteriaGroup(type="ALL", groups=[inner_group])

    dumped = outer_group.model_dump(by_alias=True)
    assert dumped["Groups"][0]["Type"] == "ANY"
    assert dumped["Groups"][0]["Count"] == 1
    assert dumped["Type"] == "ALL"


def test_criteria_group_empty_check():
    cg = CriteriaGroup()
    assert cg.is_empty() is True

    cg.groups.append(CriteriaGroup())
    assert cg.is_empty() is False


def test_demographic_criteria_stub():
    # Verify we can instantiate it
    dc = DemographicCriteria()
    assert isinstance(dc, DemographicCriteria)
