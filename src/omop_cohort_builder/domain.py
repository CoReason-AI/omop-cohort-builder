from typing import List, Optional, Union, Any, Annotated, Dict, Literal
from pydantic import Field, BeforeValidator, model_serializer
from omop_cohort_builder.base import (
    CirceModel,
    CirceCamelModel,
    TextFilter,
    NumericRange,
    DateRange,
    Window,
    ObservationFilter,
    ResultLimit,
    DateAdjustment,
    CriteriaColumn,
)


class Concept(CirceModel):
    concept_id: int = Field(alias="CONCEPT_ID")
    concept_name: str = Field(alias="CONCEPT_NAME")
    standard_concept: Optional[str] = Field(None, alias="STANDARD_CONCEPT")
    standard_concept_caption: Optional[str] = Field(
        None, alias="STANDARD_CONCEPT_CAPTION"
    )
    invalid_reason: Optional[str] = Field(None, alias="INVALID_REASON")
    invalid_reason_caption: Optional[str] = Field(None, alias="INVALID_REASON_CAPTION")
    concept_code: Optional[str] = Field(None, alias="CONCEPT_CODE")
    domain_id: Optional[str] = Field(None, alias="DOMAIN_ID")
    vocabulary_id: Optional[str] = Field(None, alias="VOCABULARY_ID")
    concept_class_id: Optional[str] = Field(None, alias="CONCEPT_CLASS_ID")


class ConceptSetItem(CirceCamelModel):
    concept: Concept
    is_excluded: bool = False
    include_descendants: bool = False
    include_mapped: bool = False


class ConceptSetExpression(CirceCamelModel):
    items: List[ConceptSetItem] = Field(default_factory=list)


class ConceptSet(CirceCamelModel):
    id: int
    name: str
    expression: ConceptSetExpression


class ConceptSetSelection(CirceModel):
    codeset_id: int
    is_exclusion: bool = False


class Occurrence(CirceModel):
    type: int
    count: int
    is_distinct: bool
    count_column: Optional[CriteriaColumn] = None


class BaseCriteria(CirceModel):
    correlated_criteria: Optional["CriteriaGroup"] = Field(
        None, alias="CorrelatedCriteria"
    )
    date_adjustment: Optional[DateAdjustment] = None


# Polymorphism helper
def criteria_deserializer(v: Any) -> Any:
    if isinstance(v, dict) and len(v) == 1:
        key = next(iter(v))
        if isinstance(v[key], dict):
            # It's a wrapped object
            new_v = v[key].copy()
            new_v["criteria_type"] = key
            return new_v
    return v


class WrappedCriteriaMixin(BaseCriteria):
    @model_serializer(mode="wrap")
    def serialize_wrapper(self, handler) -> Dict[str, Any]:
        data = handler(self)
        if "CriteriaType" in data:
            del data["CriteriaType"]
        if "criteria_type" in data:
            del data["criteria_type"]
        return {self.criteria_type: data}


class ConditionOccurrence(WrappedCriteriaMixin):
    criteria_type: Literal["ConditionOccurrence"] = "ConditionOccurrence"

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    occurrence_end_date: Optional[DateRange] = None
    condition_type: Optional[List[Concept]] = None
    condition_type_cs: Optional[ConceptSetSelection] = Field(
        None, alias="ConditionTypeCS"
    )
    condition_type_exclude: Optional[bool] = None
    stop_reason: Optional[TextFilter] = None
    condition_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(None, alias="VisitTypeCS")
    condition_status: Optional[List[Concept]] = None
    condition_status_cs: Optional[ConceptSetSelection] = Field(
        None, alias="ConditionStatusCS"
    )


class DrugExposure(WrappedCriteriaMixin):
    criteria_type: Literal["DrugExposure"] = "DrugExposure"

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    occurrence_end_date: Optional[DateRange] = None
    drug_type: Optional[List[Concept]] = None
    drug_type_cs: Optional[ConceptSetSelection] = Field(None, alias="DrugTypeCS")
    drug_type_exclude: bool = False
    stop_reason: Optional[TextFilter] = None
    refills: Optional[NumericRange] = None
    quantity: Optional[NumericRange] = None
    days_supply: Optional[NumericRange] = None
    route_concept: Optional[List[Concept]] = None
    route_concept_cs: Optional[ConceptSetSelection] = Field(
        None, alias="RouteConceptCS"
    )
    effective_drug_dose: Optional[NumericRange] = None
    dose_unit: Optional[List[Concept]] = None
    dose_unit_cs: Optional[ConceptSetSelection] = Field(None, alias="DoseUnitCS")
    lot_number: Optional[TextFilter] = None
    drug_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(None, alias="VisitTypeCS")


class VisitOccurrence(WrappedCriteriaMixin):
    criteria_type: Literal["VisitOccurrence"] = "VisitOccurrence"

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    occurrence_end_date: Optional[DateRange] = None
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(None, alias="VisitTypeCS")
    visit_type_exclude: bool = False
    visit_source_concept: Optional[int] = None
    visit_length: Optional[NumericRange] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        None, alias="ProviderSpecialtyCS"
    )
    place_of_service: Optional[List[Concept]] = None
    place_of_service_cs: Optional[ConceptSetSelection] = Field(
        None, alias="PlaceOfServiceCS"
    )
    place_of_service_location: Optional[int] = None


Criteria = Annotated[
    Union[ConditionOccurrence, DrugExposure, VisitOccurrence],
    Field(discriminator="criteria_type"),
    BeforeValidator(criteria_deserializer),
]


class WindowedCriteria(CirceModel):
    criteria: Criteria
    start_window: Window
    end_window: Window
    restrict_visit: bool = False
    ignore_observation_period: bool = False


class CorelatedCriteria(WindowedCriteria):
    occurrence: Occurrence


class CriteriaGroup(CirceModel):
    type: str = "ALL"
    count: Optional[int] = None
    criteria_list: List[CorelatedCriteria] = Field(default_factory=list)
    demographic_criteria_list: List[Any] = Field(default_factory=list)
    groups: List["CriteriaGroup"] = Field(default_factory=list)


# -- Cohort Expression Dependencies --


class CollapseSettings(CirceModel):
    collapse_type: str
    era_pad: int


class CensorWindow(CirceModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# EndStrategy Infrastruture (Polymorphic)
class WrappedStrategyMixin(CirceModel):
    """Similar to WrappedCriteriaMixin but for EndStrategy"""

    @model_serializer(mode="wrap")
    def serialize_wrapper(self, handler) -> Dict[str, Any]:
        data = handler(self)
        if "StrategyType" in data:
            del data["StrategyType"]
        if "strategy_type" in data:
            del data["strategy_type"]
        return {self.strategy_type: data}


class DateOffset(WrappedStrategyMixin):
    strategy_type: Literal["DateOffset"] = "DateOffset"
    date_field: str
    offset: int


class CustomEra(WrappedStrategyMixin):
    strategy_type: Literal["CustomEra"] = "CustomEra"
    drug_codeset_id: int
    gap_days: int
    offset: int
    days_supply_override: Optional[int] = None


# EndStrategy Helper for Polymorphism
def end_strategy_deserializer(v: Any) -> Any:
    if isinstance(v, dict) and len(v) == 1:
        key = next(iter(v))
        if isinstance(v[key], dict):
            new_v = v[key].copy()
            new_v["strategy_type"] = key
            return new_v
    return v


EndStrategy = Annotated[
    Union[DateOffset, CustomEra],
    Field(discriminator="strategy_type"),
    BeforeValidator(end_strategy_deserializer),
]


class InclusionRule(CirceCamelModel):
    name: str
    description: Optional[str] = None
    expression: CriteriaGroup


class PrimaryCriteria(CirceModel):
    criteria_list: List[Criteria]
    observation_window: ObservationFilter
    primary_limit: ResultLimit = Field(
        default_factory=ResultLimit, alias="PrimaryCriteriaLimit"
    )


class CohortExpression(CirceModel):
    title: Optional[str] = None
    primary_criteria: PrimaryCriteria
    additional_criteria: Optional[CriteriaGroup] = None
    concept_sets: List[ConceptSet] = Field(default_factory=list)
    qualified_limit: ResultLimit = Field(default_factory=ResultLimit)
    expression_limit: ResultLimit = Field(default_factory=ResultLimit)
    inclusion_rules: List[InclusionRule] = Field(default_factory=list)
    end_strategy: Optional[EndStrategy] = None
    censoring_criteria: List[Criteria] = Field(default_factory=list)
    collapse_settings: CollapseSettings = Field(
        default_factory=lambda: CollapseSettings(collapse_type="ERA", era_pad=0)
    )
    censor_window: CensorWindow = Field(default_factory=CensorWindow)
    cdm_version_range: Optional[str] = Field(None, alias="cdmVersionRange")


# Update forward refs
WindowedCriteria.model_rebuild()
BaseCriteria.model_rebuild()
ConditionOccurrence.model_rebuild()
DrugExposure.model_rebuild()
VisitOccurrence.model_rebuild()
CriteriaGroup.model_rebuild()
InclusionRule.model_rebuild()
CohortExpression.model_rebuild()
