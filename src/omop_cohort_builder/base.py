from __future__ import annotations

from enum import StrEnum
from typing import Union, Optional, ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal, to_camel as _to_camel


def to_camel(s: str) -> str:
    """
    Convert snake_case to camelCase.
    """
    return _to_camel(s)


class CirceModel(BaseModel):
    """
    Base model for all Circe objects.
    Automatically converts snake_case field names to PascalCase JSON keys.
    """

    model_config = ConfigDict(
        alias_generator=to_pascal,
        populate_by_name=True,
        extra="forbid",
    )


class CirceCamelModel(BaseModel):
    """
    Base model for objects using camelCase JSON keys (e.g., ConceptSet, InclusionRule).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class RangeType(StrEnum):
    """
    Enum for range operators.
    Java: org.ohdsi.circe.cohortdefinition.RangeType
    """

    GT = "gt"
    LT = "lt"
    EQ = "eq"
    GTE = "gte"
    LTE = "lte"
    BT = "bt"
    NOT_BT = "!bt"


class TextFilter(CirceModel):
    """
    Represents a text filter operation.
    Java: org.ohdsi.circe.cohortdefinition.TextFilter
    """

    text: str
    op: str


class NumericRange(CirceModel):
    """
    Represents a numeric range filter.
    Java: org.ohdsi.circe.cohortdefinition.NumericRange
    """

    value: Union[int, float]
    op: RangeType
    extent: Optional[Union[int, float]] = None


class DateRange(CirceModel):
    """
    Represents a date range filter.
    Java: org.ohdsi.circe.cohortdefinition.DateRange
    """

    value: str
    op: RangeType
    extent: Optional[str] = None


class Period(CirceModel):
    """
    Represents a period with start and end dates.
    Java: org.ohdsi.circe.cohortdefinition.Period
    """

    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Concept(BaseModel):
    """
    Represents an OMOP Concept.
    Java: org.ohdsi.circe.vocabulary.Concept

    Note: Uses explicit field aliases to match the SCREAMING_SNAKE_CASE
    JSON property names required by the OHDSI standard/Java implementation.
    Does not inherit from CirceModel because it does not use PascalCase.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    concept_id: int = Field(alias="CONCEPT_ID")
    concept_name: str = Field(alias="CONCEPT_NAME")
    standard_concept: Optional[str] = Field(default=None, alias="STANDARD_CONCEPT")
    standard_concept_caption: Optional[str] = Field(
        default=None, alias="STANDARD_CONCEPT_CAPTION"
    )
    invalid_reason: Optional[str] = Field(default=None, alias="INVALID_REASON")
    invalid_reason_caption: Optional[str] = Field(
        default=None, alias="INVALID_REASON_CAPTION"
    )
    concept_code: Optional[str] = Field(default=None, alias="CONCEPT_CODE")
    domain_id: Optional[str] = Field(default=None, alias="DOMAIN_ID")
    vocabulary_id: Optional[str] = Field(default=None, alias="VOCABULARY_ID")
    concept_class_id: Optional[str] = Field(default=None, alias="CONCEPT_CLASS_ID")


class ConceptSetSelection(CirceModel):
    """
    Represents a selection of a concept set.
    Java: org.ohdsi.circe.cohortdefinition.ConceptSetSelection
    """

    codeset_id: int
    is_exclusion: Optional[bool] = None


class DateAdjustment(CirceModel):
    """
    Represents a date adjustment.
    Java: org.ohdsi.circe.cohortdefinition.DateAdjustment
    """

    class DateType(StrEnum):
        START_DATE = "START_DATE"
        END_DATE = "END_DATE"

    start_with: DateType = DateType.START_DATE
    start_offset: int = 0
    end_with: DateType = DateType.END_DATE
    end_offset: int = 0


# Alias for compatibility with tests
DateAdjustmentType = DateAdjustment.DateType


class CriteriaColumn(StrEnum):
    """
    Enum for criteria columns.
    Java: org.ohdsi.circe.cohortdefinition.builders.CriteriaColumn
    """

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


class Occurrence(CirceModel):
    """
    Represents an occurrence criteria.
    Java: org.ohdsi.circe.cohortdefinition.Occurrence
    """

    EXACTLY: ClassVar[int] = 0
    AT_MOST: ClassVar[int] = 1
    AT_LEAST: ClassVar[int] = 2

    type: int
    count: int
    is_distinct: Optional[bool] = None
    count_column: Optional[CriteriaColumn] = None
