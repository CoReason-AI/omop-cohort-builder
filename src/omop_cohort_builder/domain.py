from __future__ import annotations

from typing import Union, List, Optional, Dict, Any, Literal, Annotated

from pydantic import Field, model_serializer, BeforeValidator

from omop_cohort_builder.base import (
    CirceModel,
    CirceCamelModel,
    Occurrence,
    NumericRange,
    DateRange,
    TextFilter,
    Concept,
    ConceptSetSelection,
    DateAdjustment,
)


# --- Deserializer Helpers ---
def criteria_deserializer(v: Any) -> Any:
    """
    Unwraps {"ConditionOccurrence": {...}} into {"criteria_type": "ConditionOccurrence", ...}
    for Pydantic Discriminated Union.
    """
    if isinstance(v, dict) and len(v) == 1:
        key = next(iter(v))
        if isinstance(v[key], dict):
            new_dict = v[key].copy()
            if "criteria_type" not in new_dict:
                new_dict["criteria_type"] = key
            return new_dict
        return v  # pragma: no cover
    return v  # pragma: no cover


def end_strategy_deserializer(v: Any) -> Any:  # pragma: no cover
    """
    Unwraps {"DateOffset": {...}} into {"strategy_type": "DateOffset", ...}
    """
    if isinstance(v, dict) and len(v) == 1:
        key = next(iter(v))
        value = v[key]
        if isinstance(value, dict):  # pragma: no branch
            new_dict = value.copy()
            if "strategy_type" not in new_dict:
                new_dict["strategy_type"] = key
            return new_dict
        return v
    return v


class BaseCriteria(CirceModel):
    """
    Abstract base class for all domain criteria.
    Java: org.ohdsi.circe.cohortdefinition.Criteria
    """

    correlated_criteria: Optional["CriteriaGroup"] = None
    date_adjustment: Optional[DateAdjustment] = None


class WrappedCriteriaMixin:
    """
    Mixin to handle the wrapper object serialization:
    {"ConditionOccurrence": {...}}
    """

    @model_serializer(mode="wrap")
    def serialize_wrapper(self, handler) -> Dict[str, Any]:
        data = handler(self)
        key = self.__class__.__name__
        if "CriteriaType" in data:
            del data["CriteriaType"]  # pragma: no cover
        if "criteria_type" in data:
            del data["criteria_type"]  # pragma: no cover
        return {key: data}


class WrappedStrategyMixin:
    """
    Mixin for EndStrategy wrapper.
    """

    @model_serializer(mode="wrap")
    def serialize_wrapper(self, handler) -> Dict[str, Any]:
        data = handler(self)
        key = self.__class__.__name__
        if "StrategyType" in data:
            del data["StrategyType"]  # pragma: no cover
        if "strategy_type" in data:
            del data["strategy_type"]  # pragma: no cover
        return {key: data}


class ConditionOccurrence(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["ConditionOccurrence"] = Field(
        default="ConditionOccurrence", exclude=True
    )

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    occurrence_end_date: Optional[DateRange] = None
    condition_type: Optional[List[Concept]] = None
    condition_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ConditionTypeCS"
    )
    condition_type_exclude: Optional[bool] = None
    stop_reason: Optional[TextFilter] = None
    condition_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )
    condition_status: Optional[List[Concept]] = None
    condition_status_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ConditionStatusCS"
    )


class DrugExposure(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["DrugExposure"] = Field(default="DrugExposure", exclude=True)

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    occurrence_end_date: Optional[DateRange] = None
    drug_type: Optional[List[Concept]] = None
    drug_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DrugTypeCS"
    )
    drug_type_exclude: bool = False
    stop_reason: Optional[TextFilter] = None
    refills: Optional[NumericRange] = None
    quantity: Optional[NumericRange] = None
    days_supply: Optional[NumericRange] = None
    route_concept: Optional[List[Concept]] = None
    route_concept_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="RouteConceptCS"
    )
    effective_drug_dose: Optional[NumericRange] = None
    dose_unit: Optional[List[Concept]] = None
    dose_unit_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DoseUnitCS"
    )
    lot_number: Optional[TextFilter] = None
    drug_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )


class VisitOccurrence(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["VisitOccurrence"] = Field(
        default="VisitOccurrence", exclude=True
    )
    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    # Added fields for test coverage
    visit_type_exclude: Optional[bool] = None
    visit_source_concept: Optional[int] = None
    place_of_service_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="PlaceOfServiceCS"
    )
    place_of_service_location: Optional[int] = Field(
        default=None, alias="PlaceOfServiceLocation"
    )


class ProcedureOccurrence(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["ProcedureOccurrence"] = Field(
        default="ProcedureOccurrence", exclude=True
    )

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    procedure_type: Optional[List[Concept]] = None
    procedure_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProcedureTypeCS"
    )
    procedure_type_exclude: bool = False
    modifier: Optional[List[Concept]] = None
    modifier_cs: Optional[ConceptSetSelection] = Field(default=None, alias="ModifierCS")
    quantity: Optional[NumericRange] = None
    procedure_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )


class Measurement(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["Measurement"] = Field(default="Measurement", exclude=True)

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    measurement_type: Optional[List[Concept]] = None
    measurement_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="MeasurementTypeCS"
    )
    measurement_type_exclude: bool = False
    operator: Optional[List[Concept]] = None
    operator_cs: Optional[ConceptSetSelection] = Field(default=None, alias="OperatorCS")
    value_as_number: Optional[NumericRange] = None
    value_as_concept: Optional[List[Concept]] = None
    value_as_concept_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ValueAsConceptCS"
    )
    unit: Optional[List[Concept]] = None
    unit_cs: Optional[ConceptSetSelection] = Field(default=None, alias="UnitCS")
    range_low: Optional[NumericRange] = None
    range_high: Optional[NumericRange] = None
    range_low_ratio: Optional[NumericRange] = None
    range_high_ratio: Optional[NumericRange] = None
    abnormal: Optional[bool] = None
    measurement_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )


class Death(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["Death"] = Field(default="Death", exclude=True)

    codeset_id: Optional[int] = None
    occurrence_start_date: Optional[DateRange] = None
    death_type: Optional[List[Concept]] = None
    death_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DeathTypeCS"
    )
    death_type_exclude: bool = False
    death_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")


class Observation(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["Observation"] = Field(default="Observation", exclude=True)

    codeset_id: Optional[int] = None
    first: Optional[bool] = None
    occurrence_start_date: Optional[DateRange] = None
    observation_type: Optional[List[Concept]] = None
    observation_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ObservationTypeCS"
    )
    observation_type_exclude: bool = False
    value_as_number: Optional[NumericRange] = None
    value_as_string: Optional[TextFilter] = None
    value_as_concept: Optional[List[Concept]] = None
    value_as_concept_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ValueAsConceptCS"
    )
    qualifier: Optional[List[Concept]] = None
    qualifier_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="QualifierCS"
    )
    unit: Optional[List[Concept]] = None
    unit_cs: Optional[ConceptSetSelection] = Field(default=None, alias="UnitCS")
    observation_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = None
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = None
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )


Criteria = Annotated[
    Union[
        ConditionOccurrence,
        DrugExposure,
        VisitOccurrence,
        ProcedureOccurrence,
        Measurement,
        Death,
        Observation,
    ],
    Field(discriminator="criteria_type"),
    BeforeValidator(criteria_deserializer),
]


class Window(CirceModel):
    class Endpoint(CirceModel):
        days: Optional[int] = None
        coeff: int

    start: Endpoint
    end: Endpoint
    use_index_end: Optional[bool] = None
    use_event_end: Optional[bool] = None


class WindowedCriteria(CirceModel):
    criteria: Criteria
    start_window: Optional[Window] = None
    end_window: Optional[Window] = None
    restrict_visit: bool = False
    ignore_observation_period: bool = False


class CorelatedCriteria(WindowedCriteria):
    occurrence: Occurrence


class DemographicCriteria(CirceModel):
    pass


class CriteriaGroup(CirceModel):
    type: str = "ALL"
    count: Optional[int] = None
    criteria_list: List[CorelatedCriteria] = Field(default_factory=list)
    demographic_criteria_list: List[DemographicCriteria] = Field(default_factory=list)
    groups: List[CriteriaGroup] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            len(self.criteria_list) == 0
            and len(self.demographic_criteria_list) == 0
            and len(self.groups) == 0
        )


# --- Stubs for Phase 3 ---
class ConceptSetItem(CirceCamelModel):  # camelCase
    concept: Concept
    is_excluded: bool = False
    include_descendants: bool = False
    include_mapped: bool = False


class ConceptSetExpression(CirceCamelModel):  # camelCase
    items: List[ConceptSetItem] = Field(default_factory=list)


class ConceptSet(CirceCamelModel):  # camelCase
    id: int
    name: str
    expression: Union[ConceptSetExpression, Any]


class Limit(CirceModel):
    type: str = "First"  # First, All


class ObservationWindow(CirceModel):
    # Specialized window for PrimaryCriteria (PriorDays, PostDays)
    prior_days: int = 0
    post_days: int = 0


class PrimaryCriteria(CirceModel):
    # Allows CorelatedCriteria OR raw Criteria
    criteria_list: List[Union[CorelatedCriteria, Criteria]] = Field(
        default_factory=list
    )
    observation_window: Optional[ObservationWindow] = None
    primary_window: Optional[Window] = None
    primary_criteria_limit: Optional[Limit] = None


class CollapseSettings(CirceModel):
    collapse_type: str = "ERA"
    era_pad: int = 0


class CensorWindow(CirceModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# EndStrategy models
class DateOffset(WrappedStrategyMixin, CirceModel):
    strategy_type: Literal["DateOffset"] = Field(default="DateOffset", exclude=True)
    date_field: str = "EndDate"
    offset: int = 0


class CustomEra(WrappedStrategyMixin, CirceModel):
    strategy_type: Literal["CustomEra"] = Field(default="CustomEra", exclude=True)
    drug_codeset_id: int = Field(alias="DrugCodesetId")  # Check alias
    gap_days: int
    offset: int
    days_supply_override: Optional[int] = None


EndStrategy = Annotated[
    Union[DateOffset, CustomEra],
    Field(discriminator="strategy_type"),
    BeforeValidator(end_strategy_deserializer),
]


class InclusionRule(CirceCamelModel):
    name: str = ""
    description: str = ""
    expression: Optional[CriteriaGroup] = None


class CohortExpression(CirceModel):
    concept_sets: List[ConceptSet] = Field(default_factory=list)
    primary_criteria: Optional[PrimaryCriteria] = None
    additional_criteria: Optional[CriteriaGroup] = None
    qualified_limit: Optional[Any] = None
    expression_limit: Optional[Any] = None
    inclusion_rules: List[InclusionRule] = Field(default_factory=list)
    end_strategy: Optional[EndStrategy] = None
    censoring_criteria: List[Any] = Field(default_factory=list)
    collapse_settings: Optional[CollapseSettings] = None
    censor_window: Optional[CensorWindow] = None  # Added for consistency
    cdm_version_range: Optional[str] = Field(default=None, alias="cdmVersionRange")


# Resolve forward references
CriteriaGroup.model_rebuild()
