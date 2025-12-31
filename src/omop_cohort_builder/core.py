from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


def to_pascal(snake: str) -> str:
    return "".join(word.capitalize() for word in snake.split("_"))


class CirceModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_pascal,
        populate_by_name=True,
        use_enum_values=True
    )


class TextFilter(CirceModel):
    text: str
    op: str


class NumericRange(CirceModel):
    value: float | int
    op: str
    extent: Optional[float | int] = None


class DateRange(CirceModel):
    value: str
    op: str
    extent: Optional[str] = None


class Period(CirceModel):
    start_date: str
    end_date: str


class WindowEndpoint(CirceModel):
    days: Optional[int] = None
    coeff: int


class Window(CirceModel):
    start: WindowEndpoint
    end: WindowEndpoint
    use_index_end: Optional[bool] = None
    use_event_end: Optional[bool] = None


class ObservationFilter(CirceModel):
    prior_days: int
    post_days: int


class ResultLimit(CirceModel):
    type: str = "First"


class DateAdjustmentType(str, Enum):
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"


class DateAdjustment(CirceModel):
    start_with: DateAdjustmentType = DateAdjustmentType.START_DATE
    start_offset: int = 0
    end_with: DateAdjustmentType = DateAdjustmentType.END_DATE
    end_offset: int = 0


class CriteriaColumn(str, Enum):
    DAYS_SUPPLY = "days_supply"
    DOMAIN_CONCEPT = "domain_concept_id"
    DOMAIN_SOURCE_CONCEPT = "domain_source_concept_id"
    DURATION = "duration"
    END_DATE = "end_date"
    ERA_OCCURRENCES = "occurrence_count"
    GAP_DAYS = "gap_days"
    QUANTITY = "quantity"
    RANGE_HIGH = "range_high"
    RANGE_LOW = "range_low"
    REFILLS = "refills"
    START_DATE = "start_date"
    UNIT = "unit_concept_id"
    VALUE_AS_NUMBER = "value_as_number"
    VISIT_ID = "visit_occurrence_id"
    VISIT_DETAIL_ID = "visit_detail_id"
