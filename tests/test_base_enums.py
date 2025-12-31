from __future__ import annotations

import pytest
from pydantic import ValidationError

from omop_cohort_builder.base import RangeType, NumericRange, DateRange


def test_range_type_enum_values():
    """Test that RangeType enum values match Circe expectations."""
    assert RangeType.GT == "gt"
    assert RangeType.LT == "lt"
    assert RangeType.EQ == "eq"
    assert RangeType.GTE == "gte"
    assert RangeType.LTE == "lte"
    assert RangeType.BT == "bt"
    assert RangeType.NOT_BT == "!bt"


def test_numeric_range_valid_op():
    """Test that NumericRange accepts valid operators."""
    # Using string
    nr = NumericRange(value=10, op="gt")
    assert nr.op == RangeType.GT

    # Using enum member
    nr2 = NumericRange(value=10, op=RangeType.LT)
    assert nr2.op == RangeType.LT

    # Using valid string for "not between"
    nr3 = NumericRange(value=10, op="!bt", extent=20)
    assert nr3.op == RangeType.NOT_BT


def test_numeric_range_invalid_op():
    """Test that NumericRange rejects invalid operators."""
    with pytest.raises(ValidationError) as exc:
        NumericRange(value=10, op="invalid_op")
    assert "Input should be 'gt', 'lt', 'eq', 'gte', 'lte', 'bt' or '!bt'" in str(
        exc.value
    )


def test_date_range_valid_op():
    """Test that DateRange accepts valid operators."""
    dr = DateRange(value="2020-01-01", op="eq")
    assert dr.op == RangeType.EQ

    dr2 = DateRange(value="2020-01-01", op=RangeType.GTE)
    assert dr2.op == RangeType.GTE


def test_date_range_invalid_op():
    """Test that DateRange rejects invalid operators."""
    with pytest.raises(ValidationError) as exc:
        DateRange(value="2020-01-01", op="unknown")
    assert "Input should be 'gt', 'lt', 'eq', 'gte', 'lte', 'bt' or '!bt'" in str(
        exc.value
    )
