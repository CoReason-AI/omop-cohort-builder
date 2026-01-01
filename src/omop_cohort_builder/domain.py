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
    Period,
)
from pydantic import BaseModel

"""
Domain models for OHDSI Circe Cohort Definition.

Architecture Note:
------------------
These models are designed to be functionally equivalent to the Java `org.ohdsi.circe.cohortdefinition` classes.
We use Pydantic V2 to handle serialization/deserialization with strict type safety.

Handling @JsonProperty and Case Conventions:
--------------------------------------------
1. **Snake Case vs PascalCase**:
   - Python uses `snake_case` for attribute names (e.g., `condition_source_concept`).
   - JSON (Circe standard) uses `PascalCase` (e.g., `ConditionSourceConcept`) for most Criteria fields.
   - We use `CirceModel` (defined in `base.py`) which configures Pydantic to automatically alias fields to `PascalCase`
     using `alias_generator=to_pascal`.

2. **Concept Sets & Inclusion Rules**:
   - These structures use `camelCase` in JSON (e.g., `items`, `conceptSetId`).
   - We use `CirceCamelModel` for these specific classes (e.g., `ConceptSet`, `InclusionRule`) to enforce `camelCase`.

3. **Field Aliases**:
   - Explicit `Field(alias="...")` is used when the automatic generator would fail or produce incorrect results.
     - Example: `condition_type_cs` would generate `ConditionTypeCs` (wrong) instead of `ConditionTypeCS` (correct).
     - Example: `codeset_id` in `ConditionEra` uses `CodesetId`.

4. **Polymorphism (Wrapped Objects)**:
   - Java uses `@JsonTypeInfo` to handle polymorphic lists (e.g., `List<Criteria>`).
   - Circe often wraps these in a single-key object: `{"ConditionOccurrence": {...}}`.
   - We use `Annotated[Union[...], Field(discriminator='criteria_type')]` combined with a `BeforeValidator` (`criteria_deserializer`)
     to unwrap these structures into a flat dictionary with a discriminator field for Pydantic processing.
   - We use `WrappedCriteriaMixin` with `@model_serializer(mode="wrap")` to re-wrap them during serialization.
"""


# --- Deserializer Helpers ---
def criteria_deserializer(v: Any) -> Any:
    """
    Unwraps {"ConditionOccurrence": {...}} into {"criteria_type": "ConditionOccurrence", ...}
    for Pydantic Discriminated Union.
    """
    if isinstance(v, dict):
        if len(v) == 1:
            key = next(iter(v))
            if isinstance(v[key], dict):
                new_dict = v[key].copy()
                if "criteria_type" not in new_dict:
                    new_dict["criteria_type"] = key
                return new_dict
    return v


def end_strategy_deserializer(v: Any) -> Any:
    """
    Unwraps {"DateOffset": {...}} into {"strategy_type": "DateOffset", ...}
    """
    if isinstance(v, dict):
        if len(v) == 1:
            key = next(iter(v))
            value = v[key]
            if isinstance(value, dict):
                new_dict = value.copy()
                if "strategy_type" not in new_dict:
                    new_dict["strategy_type"] = key
                return new_dict
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
        return {key: data}


class WrappedStrategyMixin:
    """
    Mixin for EndStrategy wrapper.
    """

    @model_serializer(mode="wrap")
    def serialize_wrapper(self, handler) -> Dict[str, Any]:
        data = handler(self)
        key = self.__class__.__name__
        return {key: data}


class DemographicMixin(BaseModel):
    """
    Mixin for criteria that support demographic filters (Age, Gender, Provider, Visit).
    """

    age: Optional[NumericRange] = Field(default=None, alias="Age")
    gender: Optional[List[Concept]] = Field(default=None, alias="Gender")
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty: Optional[List[Concept]] = Field(
        default=None, alias="ProviderSpecialty"
    )
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    visit_type: Optional[List[Concept]] = Field(default=None, alias="VisitType")
    visit_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitTypeCS"
    )


class OccurrenceMixin(BaseModel):
    """
    Mixin for criteria that support standard occurrence fields.
    """

    codeset_id: Optional[int] = Field(default=None, alias="CodesetId")
    first: Optional[bool] = Field(default=None, alias="First")
    occurrence_start_date: Optional[DateRange] = Field(
        default=None, alias="OccurrenceStartDate"
    )
    occurrence_end_date: Optional[DateRange] = Field(
        default=None, alias="OccurrenceEndDate"
    )


class ConditionOccurrence(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["ConditionOccurrence"] = Field(
        default="ConditionOccurrence", exclude=True
    )
    # OccurrenceMixin provides: codeset_id, first, start_date, end_date
    # DemographicMixin provides: age, gender, provider, visit_type

    condition_type: Optional[List[Concept]] = None
    condition_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ConditionTypeCS"
    )
    condition_type_exclude: Optional[bool] = None
    stop_reason: Optional[TextFilter] = None
    condition_source_concept: Optional[int] = None
    condition_status: Optional[List[Concept]] = None
    condition_status_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ConditionStatusCS"
    )


class DrugExposure(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["DrugExposure"] = Field(default="DrugExposure", exclude=True)

    drug_type: Optional[List[Concept]] = None
    drug_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DrugTypeCS"
    )
    drug_type_exclude: Optional[bool] = None
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


class VisitOccurrence(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["VisitOccurrence"] = Field(
        default="VisitOccurrence", exclude=True
    )
    visit_type_exclude: Optional[bool] = Field(default=None, alias="VisitTypeExclude")
    visit_source_concept: Optional[int] = Field(
        default=None, alias="VisitSourceConcept"
    )
    visit_length: Optional[NumericRange] = Field(default=None, alias="VisitLength")
    place_of_service: Optional[List[Concept]] = Field(
        default=None, alias="PlaceOfService"
    )
    place_of_service_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="PlaceOfServiceCS"
    )
    place_of_service_location: Optional[int] = Field(
        default=None, alias="PlaceOfServiceLocation"
    )


class ProcedureOccurrence(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["ProcedureOccurrence"] = Field(
        default="ProcedureOccurrence", exclude=True
    )

    procedure_type: Optional[List[Concept]] = None
    procedure_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProcedureTypeCS"
    )
    procedure_type_exclude: Optional[bool] = None
    modifier: Optional[List[Concept]] = None
    modifier_cs: Optional[ConceptSetSelection] = Field(default=None, alias="ModifierCS")
    quantity: Optional[NumericRange] = None
    procedure_source_concept: Optional[int] = None


class Measurement(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["Measurement"] = Field(default="Measurement", exclude=True)

    measurement_type: Optional[List[Concept]] = None
    measurement_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="MeasurementTypeCS"
    )
    measurement_type_exclude: Optional[bool] = None
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


class Death(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["Death"] = Field(default="Death", exclude=True)

    codeset_id: Optional[int] = None
    occurrence_start_date: Optional[DateRange] = None
    death_type: Optional[List[Concept]] = None
    death_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DeathTypeCS"
    )
    death_type_exclude: Optional[bool] = None
    death_source_concept: Optional[int] = None
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")


class Observation(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["Observation"] = Field(default="Observation", exclude=True)

    observation_type: Optional[List[Concept]] = None
    observation_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ObservationTypeCS"
    )
    observation_type_exclude: Optional[bool] = None
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


class EraMixin(BaseModel):
    """
    Mixin for Era-based criteria which share common era fields.
    """

    codeset_id: Optional[int] = Field(default=None, alias="CodesetId")
    first: Optional[bool] = Field(default=None, alias="First")
    era_start_date: Optional[DateRange] = Field(default=None, alias="EraStartDate")
    era_end_date: Optional[DateRange] = Field(default=None, alias="EraEndDate")
    occurrence_count: Optional[NumericRange] = Field(
        default=None, alias="OccurrenceCount"
    )
    era_length: Optional[NumericRange] = Field(default=None, alias="EraLength")
    age_at_start: Optional[NumericRange] = Field(default=None, alias="AgeAtStart")
    age_at_end: Optional[NumericRange] = Field(default=None, alias="AgeAtEnd")
    gender: Optional[List[Concept]] = Field(default=None, alias="Gender")
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")


class ConditionEra(WrappedCriteriaMixin, BaseCriteria, EraMixin):
    criteria_type: Literal["ConditionEra"] = Field(default="ConditionEra", exclude=True)


class DrugEra(WrappedCriteriaMixin, BaseCriteria, EraMixin):
    criteria_type: Literal["DrugEra"] = Field(default="DrugEra", exclude=True)

    gap_days: Optional[NumericRange] = Field(default=None, alias="GapDays")


class DoseEra(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["DoseEra"] = Field(default="DoseEra", exclude=True)
    # DoseEra does NOT support OccurrenceCount and EraLength from EraMixin?
    # Checking existing model: It DOES have EraLength, but NOT OccurrenceCount.
    # It adds Unit, DoseValue.
    # It shares Age/Gender/Dates/Codeset/First.
    # So EraMixin is partially correct but includes OccurrenceCount which DoseEra might not want?
    # Actually, looking at previous code: ConditionEra and DrugEra have OccurrenceCount. DoseEra does NOT.
    # So I should split EraMixin or override.
    # I will override occurrence_count to be excluded/None for DoseEra or just create a BaseEraMixin without it.

    # Let's verify DoseEra previous definition:
    # occurrence_count: Not present.
    # era_length: Present.

    # Re-defining EraMixin to be minimal or composition-based might be safer, but let's stick to what we can do cleanly.
    # I'll manually exclude/undefine `occurrence_count` in DoseEra or split the mixin.
    # For now, I will NOT inherit EraMixin for DoseEra to avoid pollution, but copy the fields.
    # Or better, make `CommonEraMixin` and `CountEraMixin`.

    unit: Optional[List[Concept]] = Field(default=None, alias="Unit")
    unit_cs: Optional[ConceptSetSelection] = Field(default=None, alias="UnitCS")
    dose_value: Optional[NumericRange] = Field(default=None, alias="DoseValue")
    # Redefine Era fields since we don't use EraMixin due to OccurrenceCount mismatch
    codeset_id: Optional[int] = Field(default=None, alias="CodesetId")
    first: Optional[bool] = Field(default=None, alias="First")
    era_start_date: Optional[DateRange] = Field(default=None, alias="EraStartDate")
    era_end_date: Optional[DateRange] = Field(default=None, alias="EraEndDate")
    era_length: Optional[NumericRange] = Field(default=None, alias="EraLength")
    age_at_start: Optional[NumericRange] = Field(default=None, alias="AgeAtStart")
    age_at_end: Optional[NumericRange] = Field(default=None, alias="AgeAtEnd")
    gender: Optional[List[Concept]] = Field(default=None, alias="Gender")
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")


class ObservationPeriod(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["ObservationPeriod"] = Field(
        default="ObservationPeriod", exclude=True
    )
    first: Optional[bool] = Field(default=None, alias="First")
    period_start_date: Optional[DateRange] = Field(
        default=None, alias="PeriodStartDate"
    )
    period_end_date: Optional[DateRange] = Field(default=None, alias="PeriodEndDate")
    user_defined_period: Optional[Period] = Field(
        default=None, alias="UserDefinedPeriod"
    )
    period_type: Optional[List[Concept]] = Field(default=None, alias="PeriodType")
    period_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="PeriodTypeCS"
    )
    period_length: Optional[NumericRange] = Field(default=None, alias="PeriodLength")
    age_at_start: Optional[NumericRange] = Field(default=None, alias="AgeAtStart")
    age_at_end: Optional[NumericRange] = Field(default=None, alias="AgeAtEnd")


class DeviceExposure(
    WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin
):
    criteria_type: Literal["DeviceExposure"] = Field(
        default="DeviceExposure", exclude=True
    )

    device_type: Optional[List[Concept]] = Field(default=None, alias="DeviceType")
    device_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DeviceTypeCS"
    )
    device_type_exclude: Optional[bool] = Field(default=None, alias="DeviceTypeExclude")
    unique_device_id: Optional[TextFilter] = Field(default=None, alias="UniqueDeviceId")
    quantity: Optional[NumericRange] = Field(default=None, alias="Quantity")
    device_source_concept: Optional[int] = Field(
        default=None, alias="DeviceSourceConcept"
    )


class Specimen(WrappedCriteriaMixin, BaseCriteria, OccurrenceMixin, DemographicMixin):
    criteria_type: Literal["Specimen"] = Field(default="Specimen", exclude=True)

    # Note: Specimen does not have OccurrenceEndDate in Java model, but has OccurrenceStartDate.
    # OccurrenceMixin provides both, defaulting to None. This is safe.

    specimen_type: Optional[List[Concept]] = Field(default=None, alias="SpecimenType")
    specimen_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="SpecimenTypeCS"
    )
    specimen_type_exclude: Optional[bool] = Field(
        default=None, alias="SpecimenTypeExclude"
    )
    quantity: Optional[NumericRange] = Field(default=None, alias="Quantity")
    unit: Optional[List[Concept]] = Field(default=None, alias="Unit")
    unit_cs: Optional[ConceptSetSelection] = Field(default=None, alias="UnitCS")
    anatomic_site: Optional[List[Concept]] = Field(default=None, alias="AnatomicSite")
    anatomic_site_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="AnatomicSiteCS"
    )
    disease_status: Optional[List[Concept]] = Field(default=None, alias="DiseaseStatus")
    disease_status_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="DiseaseStatusCS"
    )
    source_id: Optional[TextFilter] = Field(default=None, alias="SourceId")
    specimen_source_concept: Optional[int] = Field(
        default=None, alias="SpecimenSourceConcept"
    )


class VisitDetail(WrappedCriteriaMixin, BaseCriteria, DemographicMixin):
    # VisitDetail has custom field names (VisitDetailStartDate vs OccurrenceStartDate)
    # So it cannot simply reuse OccurrenceMixin without overriding aliases or handling it differently.
    # For now, we will NOT use OccurrenceMixin for it, but we can use DemographicMixin.
    # Wait, VisitDetail supports Age, GenderCS, ProviderSpecialtyCS, PlaceOfServiceCS
    # But DemographicMixin has "Gender" list, and "VisitType". VisitDetail might not have all of them.
    # Checking previous def: Age, GenderCS, ProviderSpecialtyCS, PlaceOfServiceCS, PlaceOfServiceLocation.
    # Missing: Gender (list), VisitType (list), VisitTypeCS, ProviderSpecialty (list).
    # So DemographicMixin is NOT a perfect fit for VisitDetail.
    # I will avoid using DemographicMixin for VisitDetail to preserve correctness.

    criteria_type: Literal["VisitDetail"] = Field(default="VisitDetail", exclude=True)

    codeset_id: Optional[int] = Field(default=None, alias="CodesetId")
    first: Optional[bool] = Field(default=None, alias="First")
    visit_detail_start_date: Optional[DateRange] = Field(
        default=None, alias="VisitDetailStartDate"
    )
    visit_detail_end_date: Optional[DateRange] = Field(
        default=None, alias="VisitDetailEndDate"
    )
    visit_detail_type_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="VisitDetailTypeCS"
    )
    visit_detail_source_concept: Optional[int] = Field(
        default=None, alias="VisitDetailSourceConcept"
    )
    visit_detail_length: Optional[NumericRange] = Field(
        default=None, alias="VisitDetailLength"
    )
    age: Optional[NumericRange] = Field(default=None, alias="Age")
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    provider_specialty_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="ProviderSpecialtyCS"
    )
    place_of_service_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="PlaceOfServiceCS"
    )
    place_of_service_location: Optional[int] = Field(
        default=None, alias="PlaceOfServiceLocation"
    )


class PayerPlanPeriod(WrappedCriteriaMixin, BaseCriteria):
    criteria_type: Literal["PayerPlanPeriod"] = Field(
        default="PayerPlanPeriod", exclude=True
    )

    first: Optional[bool] = Field(default=None, alias="First")
    period_start_date: Optional[DateRange] = Field(
        default=None, alias="PeriodStartDate"
    )
    period_end_date: Optional[DateRange] = Field(default=None, alias="PeriodEndDate")
    user_defined_period: Optional[Period] = Field(
        default=None, alias="UserDefinedPeriod"
    )
    period_length: Optional[NumericRange] = Field(default=None, alias="PeriodLength")
    age_at_start: Optional[NumericRange] = Field(default=None, alias="AgeAtStart")
    age_at_end: Optional[NumericRange] = Field(default=None, alias="AgeAtEnd")
    gender: Optional[List[Concept]] = Field(default=None, alias="Gender")
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")

    payer_concept: Optional[int] = Field(default=None, alias="PayerConcept")
    plan_concept: Optional[int] = Field(default=None, alias="PlanConcept")
    sponsor_concept: Optional[int] = Field(default=None, alias="SponsorConcept")
    stop_reason_concept: Optional[int] = Field(default=None, alias="StopReasonConcept")
    payer_source_concept: Optional[int] = Field(
        default=None, alias="PayerSourceConcept"
    )
    plan_source_concept: Optional[int] = Field(default=None, alias="PlanSourceConcept")
    sponsor_source_concept: Optional[int] = Field(
        default=None, alias="SponsorSourceConcept"
    )
    stop_reason_source_concept: Optional[int] = Field(
        default=None, alias="StopReasonSourceConcept"
    )


class GeoCriteria(WrappedCriteriaMixin, BaseCriteria):
    """
    Abstract base class for geographic criteria.
    Java: org.ohdsi.circe.cohortdefinition.GeoCriteria
    """

    start_date: Optional[DateRange] = Field(default=None, alias="StartDate")
    end_date: Optional[DateRange] = Field(default=None, alias="EndDate")


class LocationRegion(GeoCriteria):
    """
    Represents a location region criteria.
    Java: org.ohdsi.circe.cohortdefinition.LocationRegion
    """

    criteria_type: Literal["LocationRegion"] = Field(
        default="LocationRegion", exclude=True
    )
    codeset_id: Optional[int] = Field(default=None, alias="CodesetId")


class DemographicCriteria(CirceModel):
    criteria_type: Literal["DemographicCriteria"] = Field(
        default="DemographicCriteria", exclude=True
    )
    age: Optional[NumericRange] = None
    gender: Optional[List[Concept]] = None
    gender_cs: Optional[ConceptSetSelection] = Field(default=None, alias="GenderCS")
    race: Optional[List[Concept]] = None
    race_cs: Optional[ConceptSetSelection] = Field(default=None, alias="RaceCS")
    ethnicity: Optional[List[Concept]] = None
    ethnicity_cs: Optional[ConceptSetSelection] = Field(
        default=None, alias="EthnicityCS"
    )
    occurrence_start_date: Optional[DateRange] = Field(
        default=None, alias="OccurrenceStartDate"
    )
    occurrence_end_date: Optional[DateRange] = Field(
        default=None, alias="OccurrenceEndDate"
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
        ConditionEra,
        DrugEra,
        DoseEra,
        ObservationPeriod,
        DeviceExposure,
        Specimen,
        VisitDetail,
        PayerPlanPeriod,
        LocationRegion,
        DemographicCriteria,
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
    restrict_visit: Optional[bool] = Field(default=None, alias="RestrictVisit")
    ignore_observation_period: Optional[bool] = Field(
        default=None, alias="IgnoreObservationPeriod"
    )


class CorelatedCriteria(WindowedCriteria):
    occurrence: Occurrence


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
    is_excluded: Optional[bool] = None
    include_descendants: Optional[bool] = None
    include_mapped: Optional[bool] = None


class ConceptSetExpression(CirceCamelModel):  # camelCase
    items: List[ConceptSetItem] = Field(default_factory=list)


class ConceptSet(CirceCamelModel):  # camelCase
    id: int
    name: str
    expression: Union[ConceptSetExpression, Any]


class ResultLimit(CirceModel):
    type: str = "First"  # First, All


class ObservationWindow(CirceModel):
    # Specialized window for PrimaryCriteria (PriorDays, PostDays)
    prior_days: int = 0
    post_days: int = 0


class PrimaryCriteria(CirceModel):
    criteria_list: List[Criteria] = Field(default_factory=list, alias="CriteriaList")
    observation_window: Optional[ObservationWindow] = Field(
        default=None, alias="ObservationWindow"
    )
    primary_limit: ResultLimit = Field(
        default_factory=ResultLimit, alias="PrimaryCriteriaLimit"
    )


class CollapseSettings(CirceModel):
    collapse_type: str = "ERA"
    era_pad: int = 0


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
    name: Optional[str] = None
    description: Optional[str] = None
    expression: Optional[CriteriaGroup] = None


class CohortExpression(CirceModel):
    cdm_version_range: Optional[str] = Field(default=None, alias="cdmVersionRange")
    title: Optional[str] = Field(default=None, alias="Title")
    primary_criteria: PrimaryCriteria = Field(alias="PrimaryCriteria")
    additional_criteria: Optional[CriteriaGroup] = Field(
        default=None, alias="AdditionalCriteria"
    )
    concept_sets: List[ConceptSet] = Field(default_factory=list, alias="ConceptSets")
    qualified_limit: ResultLimit = Field(
        default_factory=ResultLimit, alias="QualifiedLimit"
    )
    expression_limit: ResultLimit = Field(
        default_factory=ResultLimit, alias="ExpressionLimit"
    )
    inclusion_rules: List[InclusionRule] = Field(
        default_factory=list, alias="InclusionRules"
    )
    end_strategy: Optional[EndStrategy] = Field(default=None, alias="EndStrategy")
    censoring_criteria: List[Criteria] = Field(
        default_factory=list, alias="CensoringCriteria"
    )
    collapse_settings: CollapseSettings = Field(
        default_factory=CollapseSettings, alias="CollapseSettings"
    )
    censor_window: Optional[Period] = Field(default=None, alias="CensorWindow")


# Resolve forward references
CriteriaGroup.model_rebuild()
