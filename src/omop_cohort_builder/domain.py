from typing import List, Optional, Union, Any, Annotated, Dict, Literal
from pydantic import Field, BeforeValidator, model_serializer
from omop_cohort_builder.base import (
    CirceModel,
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
        # We need to remove the discriminator field from the output if it's there.
        # Since we use by_alias=True usually, it will be "CriteriaType".
        # If by_alias=False, it is "criteria_type".
        if "CriteriaType" in data:
            del data["CriteriaType"]
        if "criteria_type" in data:
            del data["criteria_type"]

        # Wrap it in the class name (or alias if I can get it, but class name matches requirement)
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


# Update forward refs
WindowedCriteria.model_rebuild()
BaseCriteria.model_rebuild()
ConditionOccurrence.model_rebuild()
DrugExposure.model_rebuild()
VisitOccurrence.model_rebuild()
CriteriaGroup.model_rebuild()


class PrimaryCriteria(CirceModel):
    criteria_list: List[Criteria]
    observation_window: ObservationFilter
    primary_limit: ResultLimit = Field(
        default_factory=ResultLimit, alias="PrimaryCriteriaLimit"
    )
