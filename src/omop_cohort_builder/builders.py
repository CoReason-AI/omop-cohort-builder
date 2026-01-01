from __future__ import annotations

from functools import singledispatchmethod
from typing import Dict, List

from sqlalchemy import select, Select

from omop_cohort_builder.domain import (
    ConditionOccurrence,
    ConditionEra,
    DrugEra,
    DoseEra,
    DrugExposure,
    VisitOccurrence,
    ProcedureOccurrence,
    Measurement,
    Observation,
    DeviceExposure,
    Death,
    Specimen,
    VisitDetail,
    ObservationPeriod,
    PayerPlanPeriod,
    LocationRegion,
    DemographicCriteria,
    Criteria,
)
from omop_cohort_builder.schema import (
    condition_occurrence,
    condition_era,
    drug_era,
    dose_era,
    drug_exposure,
    visit_occurrence,
    procedure_occurrence,
    measurement,
    observation,
    device_exposure,
    death,
    specimen,
    visit_detail,
    observation_period,
    payer_plan_period,
    location_history,
    location,
    person,
)


class QueryBuilder:
    """
    Builds SQL queries from Circe criteria models.
    """

    def __init__(self, concept_set_map: Dict[int, List[int]] | None = None):
        """
        Args:
            concept_set_map: A dictionary mapping codeset IDs to lists of concept IDs.
                             Used to resolve 'codeset_id' fields in criteria.
        """
        self.concept_set_map = concept_set_map or {}

    def _resolve_codeset(self, codeset_id: int) -> List[int]:
        """
        Resolves a codeset ID to a list of concept IDs.
        If the codeset ID is not found, returns an empty list.
        """
        return self.concept_set_map.get(codeset_id, [])

    def _apply_codeset_filter(self, query, column, codeset_id: int | None):
        """Helper to apply standard codeset ID filter."""
        if codeset_id is not None:
            concept_ids = self._resolve_codeset(codeset_id)
            return query.where(column.in_(concept_ids))
        return query

    def _apply_concept_list_filter(
        self, query, column, concepts: List | None, exclude: bool | None = False
    ):
        """
        Helper to apply List[Concept] filters, handling optional exclusion logic.
        """
        if concepts:
            concept_ids = [c.concept_id for c in concepts]
            if exclude:
                return query.where(column.notin_(concept_ids))
            else:
                return query.where(column.in_(concept_ids))
        return query

    def _apply_equality_filter(self, query, column, value: int | None):
        """Helper to apply simple equality check if value is not None."""
        if value is not None:
            return query.where(column == value)
        return query

    @singledispatchmethod
    def build_criteria(self, criteria: Criteria) -> Select:
        """
        Dispatches the build call to the appropriate method based on the criteria type.
        """
        raise NotImplementedError(
            f"Query builder not implemented for type: {type(criteria)}"
        )

    @build_criteria.register
    def _build_condition_occurrence(self, criteria: ConditionOccurrence) -> Select:
        """
        Builds a SQL query for ConditionOccurrence criteria.
        """
        query = select(condition_occurrence)

        # 0. Codeset ID -> condition_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, condition_occurrence.c.condition_concept_id, criteria.codeset_id
        )

        # 1. Condition Type (List of Concepts) -> condition_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            condition_occurrence.c.condition_type_concept_id,
            criteria.condition_type,
            exclude=criteria.condition_type_exclude,
        )

        # 1b. Condition Type (ConceptSetSelection)
        query = self._apply_concept_set_selection(
            query,
            condition_occurrence.c.condition_type_concept_id,
            criteria.condition_type_cs,
        )

        # 2. Condition Source Concept -> condition_source_concept_id = ...
        query = self._apply_equality_filter(
            query,
            condition_occurrence.c.condition_source_concept_id,
            criteria.condition_source_concept,
        )

        # 3. Stop Reason (TextFilter)
        if criteria.stop_reason:
            query = self._apply_text_filter(
                query, condition_occurrence.c.stop_reason, criteria.stop_reason
            )

        # 4. Condition Status (List of Concepts)
        query = self._apply_concept_list_filter(
            query,
            condition_occurrence.c.condition_status_concept_id,
            criteria.condition_status,
        )

        # 4b. Condition Status (ConceptSetSelection)
        query = self._apply_concept_set_selection(
            query,
            condition_occurrence.c.condition_status_concept_id,
            criteria.condition_status_cs,
        )

        return query

    @build_criteria.register
    def _build_condition_era(self, criteria: ConditionEra) -> Select:
        """
        Builds a SQL query for ConditionEra criteria.
        """
        query = select(condition_era)

        # 0. Codeset ID -> condition_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, condition_era.c.condition_concept_id, criteria.codeset_id
        )

        # 1. Era Start Date -> condition_era_start_date
        if criteria.era_start_date:
            query = self._apply_date_filter(
                query,
                condition_era.c.condition_era_start_date,
                criteria.era_start_date,
            )

        # 2. Era End Date -> condition_era_end_date
        if criteria.era_end_date:
            query = self._apply_date_filter(
                query,
                condition_era.c.condition_era_end_date,
                criteria.era_end_date,
            )

        # 3. Occurrence Count -> condition_occurrence_count
        if criteria.occurrence_count:
            query = self._apply_numeric_filter(
                query,
                condition_era.c.condition_occurrence_count,
                criteria.occurrence_count,
            )

        # 4. Era Length -> (condition_era_end_date - condition_era_start_date)
        if criteria.era_length:
            length_expr = (
                condition_era.c.condition_era_end_date
                - condition_era.c.condition_era_start_date
            )
            query = self._apply_numeric_filter(query, length_expr, criteria.era_length)

        # TODO: Implement age_at_start, age_at_end, gender (requires Person table join)

        return query

    @build_criteria.register
    def _build_drug_era(self, criteria: DrugEra) -> Select:
        """
        Builds a SQL query for DrugEra criteria.
        """
        query = select(drug_era)

        # 0. Codeset ID -> drug_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, drug_era.c.drug_concept_id, criteria.codeset_id
        )

        # 1. Era Start Date -> drug_era_start_date
        if criteria.era_start_date:
            query = self._apply_date_filter(
                query,
                drug_era.c.drug_era_start_date,
                criteria.era_start_date,
            )

        # 2. Era End Date -> drug_era_end_date
        if criteria.era_end_date:
            query = self._apply_date_filter(
                query,
                drug_era.c.drug_era_end_date,
                criteria.era_end_date,
            )

        # 3. Occurrence Count -> drug_exposure_count
        if criteria.occurrence_count:
            query = self._apply_numeric_filter(
                query,
                drug_era.c.drug_exposure_count,
                criteria.occurrence_count,
            )

        # 4. Gap Days -> gap_days
        if criteria.gap_days:
            query = self._apply_numeric_filter(
                query,
                drug_era.c.gap_days,
                criteria.gap_days,
            )

        # 5. Era Length -> (drug_era_end_date - drug_era_start_date)
        if criteria.era_length:
            length_expr = drug_era.c.drug_era_end_date - drug_era.c.drug_era_start_date
            query = self._apply_numeric_filter(query, length_expr, criteria.era_length)

        # TODO: Implement age_at_start, age_at_end, gender (requires Person table join)

        return query

    @build_criteria.register
    def _build_dose_era(self, criteria: DoseEra) -> Select:
        """
        Builds a SQL query for DoseEra criteria.
        """
        query = select(dose_era)

        # 0. Codeset ID -> drug_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, dose_era.c.drug_concept_id, criteria.codeset_id
        )

        # 1. Era Start Date -> dose_era_start_date
        if criteria.era_start_date:
            query = self._apply_date_filter(
                query,
                dose_era.c.dose_era_start_date,
                criteria.era_start_date,
            )

        # 2. Era End Date -> dose_era_end_date
        if criteria.era_end_date:
            query = self._apply_date_filter(
                query,
                dose_era.c.dose_era_end_date,
                criteria.era_end_date,
            )

        # 3. Dose Value -> dose_value
        if criteria.dose_value:
            query = self._apply_numeric_filter(
                query,
                dose_era.c.dose_value,
                criteria.dose_value,
            )

        # 4. Era Length -> (dose_era_end_date - dose_era_start_date)
        if criteria.era_length:
            length_expr = dose_era.c.dose_era_end_date - dose_era.c.dose_era_start_date
            query = self._apply_numeric_filter(query, length_expr, criteria.era_length)

        # 5. Unit (List of Concepts) -> unit_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, dose_era.c.unit_concept_id, criteria.unit
        )

        # TODO: Implement unit_cs (ConceptSetSelection)
        # TODO: Implement age_at_start, age_at_end, gender (requires Person table join)

        return query

    @build_criteria.register
    def _build_specimen(self, criteria: Specimen) -> Select:
        """
        Builds a SQL query for Specimen criteria.
        """
        query = select(specimen)

        # 0. Codeset ID -> specimen_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, specimen.c.specimen_concept_id, criteria.codeset_id
        )

        # 1. Specimen Type (List of Concepts) -> specimen_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            specimen.c.specimen_type_concept_id,
            criteria.specimen_type,
            exclude=criteria.specimen_type_exclude,
        )

        # 2. Quantity (NumericRange)
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, specimen.c.quantity, criteria.quantity
            )

        # 3. Unit (List of Concepts) -> unit_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, specimen.c.unit_concept_id, criteria.unit
        )

        # 4. Anatomic Site (List of Concepts) -> anatomic_site_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, specimen.c.anatomic_site_concept_id, criteria.anatomic_site
        )

        # 5. Disease Status (List of Concepts) -> disease_status_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, specimen.c.disease_status_concept_id, criteria.disease_status
        )

        # 6. Source ID (TextFilter) -> specimen_source_id LIKE ...
        if criteria.source_id:
            query = self._apply_text_filter(
                query, specimen.c.specimen_source_id, criteria.source_id
            )

        # 7. Occurrence Start Date -> specimen_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query, specimen.c.specimen_date, criteria.occurrence_start_date
            )

        return query

    @build_criteria.register
    def _build_device_exposure(self, criteria: DeviceExposure) -> Select:
        """
        Builds a SQL query for DeviceExposure criteria.
        """
        query = select(device_exposure)

        # 0. Codeset ID -> device_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, device_exposure.c.device_concept_id, criteria.codeset_id
        )

        # 1. Device Type (List of Concepts) -> device_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            device_exposure.c.device_type_concept_id,
            criteria.device_type,
            exclude=criteria.device_type_exclude,
        )

        # 2. Unique Device ID (TextFilter)
        if criteria.unique_device_id:
            query = self._apply_text_filter(
                query, device_exposure.c.unique_device_id, criteria.unique_device_id
            )

        # 3. Quantity (NumericRange)
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, device_exposure.c.quantity, criteria.quantity
            )

        # 4. Device Source Concept (int)
        query = self._apply_equality_filter(
            query,
            device_exposure.c.device_source_concept_id,
            criteria.device_source_concept,
        )

        # 5. Occurrence Start Date -> device_exposure_start_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                device_exposure.c.device_exposure_start_date,
                criteria.occurrence_start_date,
            )

        # 6. Occurrence End Date -> device_exposure_end_date
        if criteria.occurrence_end_date:
            query = self._apply_date_filter(
                query,
                device_exposure.c.device_exposure_end_date,
                criteria.occurrence_end_date,
            )

        return query

    @build_criteria.register
    def _build_observation(self, criteria: Observation) -> Select:
        """
        Builds a SQL query for Observation criteria.
        """
        query = select(observation)

        # 0. Codeset ID -> observation_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, observation.c.observation_concept_id, criteria.codeset_id
        )

        # 1. Observation Type (List of Concepts)
        query = self._apply_concept_list_filter(
            query,
            observation.c.observation_type_concept_id,
            criteria.observation_type,
            exclude=criteria.observation_type_exclude,
        )

        # 2. Value As Number (NumericRange)
        if criteria.value_as_number:
            query = self._apply_numeric_filter(
                query, observation.c.value_as_number, criteria.value_as_number
            )

        # 3. Value As String (TextFilter)
        if criteria.value_as_string:
            query = self._apply_text_filter(
                query, observation.c.value_as_string, criteria.value_as_string
            )

        # 4. Value As Concept (List of Concepts)
        query = self._apply_concept_list_filter(
            query, observation.c.value_as_concept_id, criteria.value_as_concept
        )

        # 5. Qualifier (List of Concepts)
        query = self._apply_concept_list_filter(
            query, observation.c.qualifier_concept_id, criteria.qualifier
        )

        # 6. Unit (List of Concepts)
        query = self._apply_concept_list_filter(
            query, observation.c.unit_concept_id, criteria.unit
        )

        # 7. Observation Source Concept (int)
        query = self._apply_equality_filter(
            query,
            observation.c.observation_source_concept_id,
            criteria.observation_source_concept,
        )

        # 8. Occurrence Start Date -> observation_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query, observation.c.observation_date, criteria.occurrence_start_date
            )

        return query

    @build_criteria.register
    def _build_measurement(self, criteria: Measurement) -> Select:
        """
        Builds a SQL query for Measurement criteria.
        """
        query = select(measurement)

        # 0. Codeset ID -> measurement_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, measurement.c.measurement_concept_id, criteria.codeset_id
        )

        # 1. Measurement Type (List of Concepts) -> measurement_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            measurement.c.measurement_type_concept_id,
            criteria.measurement_type,
            exclude=criteria.measurement_type_exclude,
        )

        # 2. Operator (List of Concepts) -> operator_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, measurement.c.operator_concept_id, criteria.operator
        )

        # 3. Value As Number (NumericRange)
        if criteria.value_as_number:
            query = self._apply_numeric_filter(
                query, measurement.c.value_as_number, criteria.value_as_number
            )

        # 4. Value As Concept (List of Concepts) -> value_as_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, measurement.c.value_as_concept_id, criteria.value_as_concept
        )

        # 5. Unit (List of Concepts) -> unit_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, measurement.c.unit_concept_id, criteria.unit
        )

        # 6. Range Low (NumericRange)
        if criteria.range_low:
            query = self._apply_numeric_filter(
                query, measurement.c.range_low, criteria.range_low
            )

        # 7. Range High (NumericRange)
        if criteria.range_high:
            query = self._apply_numeric_filter(
                query, measurement.c.range_high, criteria.range_high
            )

        # 8. Range Low Ratio (NumericRange) -> (value_as_number / range_low)
        # Note: We use NULLIF to avoid divide by zero errors, mirroring Java behavior implicitly or explicitly.
        # However, SQLAlchemy's NULLIF support depends on dialect. Standard SQL 'NULLIF' is widely supported.
        if criteria.range_low_ratio:
            # We need to construct the expression: value_as_number / NULLIF(range_low, 0)
            # Since we are using Core, we can import func
            from sqlalchemy import func

            ratio_expr = measurement.c.value_as_number / func.nullif(
                measurement.c.range_low, 0
            )
            query = self._apply_numeric_filter(
                query, ratio_expr, criteria.range_low_ratio
            )

        # 9. Range High Ratio (NumericRange) -> (value_as_number / range_high)
        if criteria.range_high_ratio:
            from sqlalchemy import func

            ratio_expr = measurement.c.value_as_number / func.nullif(
                measurement.c.range_high, 0
            )
            query = self._apply_numeric_filter(
                query, ratio_expr, criteria.range_high_ratio
            )

        # 10. Abnormal (bool)
        if criteria.abnormal:
            # Java: (C.value_as_number < C.range_low or C.value_as_number > C.range_high or C.value_as_concept_id in (4155142, 4155143))
            from sqlalchemy import or_

            abnormal_expr = or_(
                measurement.c.value_as_number < measurement.c.range_low,
                measurement.c.value_as_number > measurement.c.range_high,
                measurement.c.value_as_concept_id.in_([4155142, 4155143]),
            )
            query = query.where(abnormal_expr)

        # 11. Measurement Source Concept (int)
        query = self._apply_equality_filter(
            query,
            measurement.c.measurement_source_concept_id,
            criteria.measurement_source_concept,
        )

        # 12. Occurrence Start Date -> measurement_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query, measurement.c.measurement_date, criteria.occurrence_start_date
            )

        return query

    @build_criteria.register
    def _build_death(self, criteria: Death) -> Select:
        """
        Builds a SQL query for Death criteria.
        """
        query = select(death)

        # 0. Codeset ID -> cause_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, death.c.cause_concept_id, criteria.codeset_id
        )

        # 1. Death Type (List of Concepts) -> death_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            death.c.death_type_concept_id,
            criteria.death_type,
            exclude=criteria.death_type_exclude,
        )

        # 2. Death Source Concept (int) -> cause_source_concept_id = ...
        query = self._apply_equality_filter(
            query, death.c.cause_source_concept_id, criteria.death_source_concept
        )

        # 3. Occurrence Start Date -> death_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query, death.c.death_date, criteria.occurrence_start_date
            )

        return query

    @build_criteria.register
    def _build_drug_exposure(self, criteria: DrugExposure) -> Select:
        """
        Builds a SQL query for DrugExposure criteria.
        """
        query = select(drug_exposure)

        # 0. Codeset ID -> drug_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, drug_exposure.c.drug_concept_id, criteria.codeset_id
        )

        # 1. Occurrence Start Date -> drug_exposure_start_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                drug_exposure.c.drug_exposure_start_date,
                criteria.occurrence_start_date,
            )

        # 2. Occurrence End Date -> drug_exposure_end_date
        if criteria.occurrence_end_date:
            query = self._apply_date_filter(
                query,
                drug_exposure.c.drug_exposure_end_date,
                criteria.occurrence_end_date,
            )

        # 3. Drug Type (List of Concepts) -> drug_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            drug_exposure.c.drug_type_concept_id,
            criteria.drug_type,
            exclude=criteria.drug_type_exclude,
        )

        # TODO: Implement drug_type_cs (ConceptSet)

        # 4. Stop Reason (TextFilter) -> stop_reason LIKE ...
        if criteria.stop_reason:
            query = self._apply_text_filter(
                query, drug_exposure.c.stop_reason, criteria.stop_reason
            )

        # 5. Refills (NumericRange) -> refills op value
        if criteria.refills:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.refills, criteria.refills
            )

        # 6. Quantity (NumericRange) -> quantity op value
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.quantity, criteria.quantity
            )

        # 7. Days Supply (NumericRange) -> days_supply op value
        if criteria.days_supply:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.days_supply, criteria.days_supply
            )

        # 8. Route Concept (List of Concepts) -> route_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, drug_exposure.c.route_concept_id, criteria.route_concept
        )

        # TODO: Implement route_concept_cs

        # 9. Lot Number (TextFilter) -> lot_number LIKE ...
        if criteria.lot_number:
            query = self._apply_text_filter(
                query, drug_exposure.c.lot_number, criteria.lot_number
            )

        # 10. Drug Source Concept (int) -> drug_source_concept_id = ...
        query = self._apply_equality_filter(
            query,
            drug_exposure.c.drug_source_concept_id,
            criteria.drug_source_concept,
        )

        # 11. Dose Unit (List of Concepts)
        if criteria.dose_unit:
            pass

        # 12. Age (NumericRange) -> (Year(drug_exposure_start_date) - person.year_of_birth)
        # 13. Gender (List of Concepts) -> person.gender_concept_id
        if criteria.age or criteria.gender:
            # We need to join with the PERSON table
            # drug_exposure.person_id == person.person_id
            query = query.join(person, drug_exposure.c.person_id == person.c.person_id)

            if criteria.age:
                from sqlalchemy import extract

                # Age calculation: year(start_date) - year_of_birth
                # Note: This is a simplified "Age in Years" calculation common in OMOP/OHDSI
                age_expr = (
                    extract("year", drug_exposure.c.drug_exposure_start_date)
                    - person.c.year_of_birth
                )
                query = self._apply_numeric_filter(query, age_expr, criteria.age)

            if criteria.gender:
                concept_ids = [c.concept_id for c in criteria.gender]
                query = query.where(person.c.gender_concept_id.in_(concept_ids))

        return query

    @build_criteria.register
    def _build_visit_occurrence(self, criteria: VisitOccurrence) -> Select:
        """
        Builds a SQL query for VisitOccurrence criteria.
        """
        query = select(visit_occurrence)

        # 0. Codeset ID -> visit_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, visit_occurrence.c.visit_concept_id, criteria.codeset_id
        )

        # 1. Visit Type (List of Concepts) -> visit_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            visit_occurrence.c.visit_type_concept_id,
            criteria.visit_type,
            exclude=criteria.visit_type_exclude,
        )

        # 2. Visit Source Concept -> visit_source_concept_id = ...
        query = self._apply_equality_filter(
            query,
            visit_occurrence.c.visit_source_concept_id,
            criteria.visit_source_concept,
        )

        # 3. Occurrence Start Date -> visit_start_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                visit_occurrence.c.visit_start_date,
                criteria.occurrence_start_date,
            )

        # 4. Occurrence End Date -> visit_end_date
        if criteria.occurrence_end_date:
            query = self._apply_date_filter(
                query, visit_occurrence.c.visit_end_date, criteria.occurrence_end_date
            )

        # 5. Visit Length -> (visit_end_date - visit_start_date)
        if criteria.visit_length:
            length_expr = (
                visit_occurrence.c.visit_end_date - visit_occurrence.c.visit_start_date
            )
            query = self._apply_numeric_filter(
                query, length_expr, criteria.visit_length
            )

        return query

    @build_criteria.register
    def _build_procedure_occurrence(self, criteria: ProcedureOccurrence) -> Select:
        """
        Builds a SQL query for ProcedureOccurrence criteria.
        """
        query = select(procedure_occurrence)

        # 0. Codeset ID -> procedure_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, procedure_occurrence.c.procedure_concept_id, criteria.codeset_id
        )

        # 1. Procedure Type (List of Concepts) -> procedure_type_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query,
            procedure_occurrence.c.procedure_type_concept_id,
            criteria.procedure_type,
            exclude=criteria.procedure_type_exclude,
        )

        # 2. Modifier (List of Concepts) -> modifier_concept_id IN (...)
        query = self._apply_concept_list_filter(
            query, procedure_occurrence.c.modifier_concept_id, criteria.modifier
        )

        # 3. Quantity (NumericRange) -> quantity op value
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, procedure_occurrence.c.quantity, criteria.quantity
            )

        # 4. Procedure Source Concept -> procedure_source_concept_id = ...
        query = self._apply_equality_filter(
            query,
            procedure_occurrence.c.procedure_source_concept_id,
            criteria.procedure_source_concept,
        )

        # 5. Occurrence Start Date -> procedure_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                procedure_occurrence.c.procedure_date,
                criteria.occurrence_start_date,
            )

        return query

    @build_criteria.register
    def _build_visit_detail(self, criteria: VisitDetail) -> Select:
        """
        Builds a SQL query for VisitDetail criteria.
        """
        query = select(visit_detail)

        # 0. Codeset ID -> visit_detail_concept_id IN (...)
        query = self._apply_codeset_filter(
            query, visit_detail.c.visit_detail_concept_id, criteria.codeset_id
        )

        # 1. Visit Detail Source Concept -> visit_detail_source_concept_id = ...
        query = self._apply_equality_filter(
            query,
            visit_detail.c.visit_detail_source_concept_id,
            criteria.visit_detail_source_concept,
        )

        # 2. Visit Detail Start Date -> visit_detail_start_date
        if criteria.visit_detail_start_date:
            query = self._apply_date_filter(
                query,
                visit_detail.c.visit_detail_start_date,
                criteria.visit_detail_start_date,
            )

        # 3. Visit Detail End Date -> visit_detail_end_date
        if criteria.visit_detail_end_date:
            query = self._apply_date_filter(
                query,
                visit_detail.c.visit_detail_end_date,
                criteria.visit_detail_end_date,
            )

        # 4. Visit Detail Length -> (visit_detail_end_date - visit_detail_start_date)
        if criteria.visit_detail_length:
            length_expr = (
                visit_detail.c.visit_detail_end_date
                - visit_detail.c.visit_detail_start_date
            )
            query = self._apply_numeric_filter(
                query, length_expr, criteria.visit_detail_length
            )

        # TODO: Implement visit_detail_type_cs (ConceptSetSelection)
        # TODO: Implement age, gender_cs, provider_specialty_cs, place_of_service_cs (requires joins)

        return query

    @build_criteria.register
    def _build_observation_period(self, criteria: ObservationPeriod) -> Select:
        """
        Builds a SQL query for ObservationPeriod criteria.
        """
        query = select(observation_period)

        # ObservationPeriod typically doesn't use codeset_id for the primary table filtering like others.
        # It's about time periods.

        # 1. Period Start Date -> observation_period_start_date
        if criteria.period_start_date:
            query = self._apply_date_filter(
                query,
                observation_period.c.observation_period_start_date,
                criteria.period_start_date,
            )

        # 2. Period End Date -> observation_period_end_date
        if criteria.period_end_date:
            query = self._apply_date_filter(
                query,
                observation_period.c.observation_period_end_date,
                criteria.period_end_date,
            )

        # 3. Period Type (List of Concepts) -> period_type_concept_id IN (...)
        if criteria.period_type:
            concept_ids = [c.concept_id for c in criteria.period_type]
            query = query.where(
                observation_period.c.period_type_concept_id.in_(concept_ids)
            )

        # 4. Period Length -> (observation_period_end_date - observation_period_start_date)
        if criteria.period_length:
            length_expr = (
                observation_period.c.observation_period_end_date
                - observation_period.c.observation_period_start_date
            )
            query = self._apply_numeric_filter(
                query, length_expr, criteria.period_length
            )

        # TODO: Implement user_defined_period (requires complex logic)
        # TODO: Implement period_type_cs (ConceptSetSelection)
        # TODO: Implement age_at_start, age_at_end (requires Person join)

        return query

    @build_criteria.register
    def _build_payer_plan_period(self, criteria: PayerPlanPeriod) -> Select:
        """
        Builds a SQL query for PayerPlanPeriod criteria.
        """
        query = select(payer_plan_period)

        # 1. Period Start Date -> payer_plan_period_start_date
        if criteria.period_start_date:
            query = self._apply_date_filter(
                query,
                payer_plan_period.c.payer_plan_period_start_date,
                criteria.period_start_date,
            )

        # 2. Period End Date -> payer_plan_period_end_date
        if criteria.period_end_date:
            query = self._apply_date_filter(
                query,
                payer_plan_period.c.payer_plan_period_end_date,
                criteria.period_end_date,
            )

        # 3. Period Length -> (payer_plan_period_end_date - payer_plan_period_start_date)
        if criteria.period_length:
            length_expr = (
                payer_plan_period.c.payer_plan_period_end_date
                - payer_plan_period.c.payer_plan_period_start_date
            )
            query = self._apply_numeric_filter(
                query, length_expr, criteria.period_length
            )

        # 4. Payer Source Concept -> payer_source_concept_id
        if criteria.payer_source_concept is not None:
            query = query.where(
                payer_plan_period.c.payer_source_concept_id
                == criteria.payer_source_concept
            )

        # 5. Plan Source Concept -> plan_source_concept_id
        if criteria.plan_source_concept is not None:
            query = query.where(
                payer_plan_period.c.plan_source_concept_id
                == criteria.plan_source_concept
            )

        # 6. Sponsor Source Concept -> sponsor_source_concept_id
        if criteria.sponsor_source_concept is not None:
            query = query.where(
                payer_plan_period.c.sponsor_source_concept_id
                == criteria.sponsor_source_concept
            )

        # 7. Stop Reason Source Concept -> stop_reason_source_concept_id
        if criteria.stop_reason_source_concept is not None:
            query = query.where(
                payer_plan_period.c.stop_reason_source_concept_id
                == criteria.stop_reason_source_concept
            )

        # TODO: Implement user_defined_period (requires complex logic)
        # TODO: Implement age_at_start, age_at_end, gender (requires Person join)
        # TODO: Implement payer_concept, plan_concept, sponsor_concept, stop_reason_concept
        # (These columns are not standard in OMOP CDM v5.4 payer_plan_period table,
        # but exist in the Criteria model.)

        return query

    @build_criteria.register
    def _build_location_region(self, criteria: LocationRegion) -> Select:
        """
        Builds a SQL query for LocationRegion criteria.

        Logic:
        1. Query LOCATION_HISTORY table.
        2. Join with LOCATION table on location_id.
        3. Filter by start_date and end_date (from GeoCriteria parent).
        4. Filter by codeset_id (implicit filtering of region_concept_id).
        """
        # Join location_history -> location
        query = select(location_history).join(
            location, location_history.c.location_id == location.c.location_id
        )

        # Ensure we only select PERSON history records
        query = query.where(location_history.c.domain_id == "PERSON")

        # 1. Start Date -> location_history.start_date
        if criteria.start_date:
            query = self._apply_date_filter(
                query,
                location_history.c.start_date,
                criteria.start_date,
            )

        # 2. End Date -> location_history.end_date
        if criteria.end_date:
            query = self._apply_date_filter(
                query,
                location_history.c.end_date,
                criteria.end_date,
            )

        # 3. Codeset ID (Region Concept)
        if criteria.codeset_id is not None:
            # Resolve codeset_id to concept_ids
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            # Filter location.region_concept_id
            query = query.where(location.c.region_concept_id.in_(concept_ids))

        return query

    @build_criteria.register
    def _build_demographic_criteria(self, criteria: DemographicCriteria) -> Select:
        """
        Builds a SQL query for DemographicCriteria.

        Logic:
        1. Query OBSERVATION_PERIOD table (implied event stream).
        2. Join with PERSON table to filter demographics.
        3. Filter by Age, Gender, Race, Ethnicity.
        4. Filter by Observation Period Start/End dates.
        """
        query = select(observation_period).join(
            person, observation_period.c.person_id == person.c.person_id
        )

        # 1. Age (NumericRange) -> (Year(observation_period_start_date) - person.year_of_birth)
        if criteria.age:
            from sqlalchemy import extract

            age_expr = (
                extract("year", observation_period.c.observation_period_start_date)
                - person.c.year_of_birth
            )
            query = self._apply_numeric_filter(query, age_expr, criteria.age)

        # 2. Gender (List of Concepts) -> person.gender_concept_id
        query = self._apply_concept_list_filter(
            query, person.c.gender_concept_id, criteria.gender
        )

        # TODO: Implement gender_cs (ConceptSetSelection)

        # 3. Race (List of Concepts) -> person.race_concept_id
        query = self._apply_concept_list_filter(
            query, person.c.race_concept_id, criteria.race
        )

        # TODO: Implement race_cs (ConceptSetSelection)

        # 4. Ethnicity (List of Concepts) -> person.ethnicity_concept_id
        query = self._apply_concept_list_filter(
            query, person.c.ethnicity_concept_id, criteria.ethnicity
        )

        # TODO: Implement ethnicity_cs (ConceptSetSelection)

        # 5. Occurrence Start Date -> observation_period_start_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                observation_period.c.observation_period_start_date,
                criteria.occurrence_start_date,
            )

        # 6. Occurrence End Date -> observation_period_end_date
        if criteria.occurrence_end_date:
            query = self._apply_date_filter(
                query,
                observation_period.c.observation_period_end_date,
                criteria.occurrence_end_date,
            )

        return query

    def _apply_numeric_filter(self, query, column, criteria_range):
        """Helper to apply numeric range filters."""
        if criteria_range.op == "gt":
            return query.where(column > criteria_range.value)
        elif criteria_range.op == "lt":
            return query.where(column < criteria_range.value)
        elif criteria_range.op == "eq":
            return query.where(column == criteria_range.value)
        elif criteria_range.op == "gte":
            return query.where(column >= criteria_range.value)
        elif criteria_range.op == "lte":
            return query.where(column <= criteria_range.value)
        elif criteria_range.op == "bt":  # Between
            if criteria_range.extent is not None:
                return query.where(
                    column.between(criteria_range.value, criteria_range.extent)
                )
        elif criteria_range.op == "!bt":  # Not Between
            if criteria_range.extent is not None:
                return query.where(
                    ~column.between(criteria_range.value, criteria_range.extent)
                )
        return query

    def _apply_date_filter(self, query, column, criteria_range):
        """Helper to apply date range filters."""
        if criteria_range.op == "gt":
            return query.where(column > criteria_range.value)
        elif criteria_range.op == "lt":
            return query.where(column < criteria_range.value)
        elif criteria_range.op == "eq":
            return query.where(column == criteria_range.value)
        elif criteria_range.op == "gte":
            return query.where(column >= criteria_range.value)
        elif criteria_range.op == "lte":
            return query.where(column <= criteria_range.value)
        elif criteria_range.op == "bt":  # Between
            if criteria_range.extent is not None:
                return query.where(
                    column.between(criteria_range.value, criteria_range.extent)
                )
        elif criteria_range.op == "!bt":  # Not Between
            if criteria_range.extent is not None:
                return query.where(
                    ~column.between(criteria_range.value, criteria_range.extent)
                )
        return query

    def _apply_text_filter(self, query, column, text_filter):
        """Helper to apply text filters with correct wildcard injection."""
        text = text_filter.text
        op = text_filter.op

        if op in ("=", "eq"):
            return query.where(column == text)
        elif op == "contains":
            return query.where(column.like(f"%{text}%"))
        elif op == "startsWith":
            return query.where(column.like(f"{text}%"))
        elif op == "endsWith":
            return query.where(column.like(f"%{text}"))
        elif op == "!eq":
            return query.where(column != text)
        elif op == "!contains":
            return query.where(~column.like(f"%{text}%"))
        elif op == "!startsWith":
            return query.where(~column.like(f"{text}%"))
        elif op == "!endsWith":
            return query.where(~column.like(f"%{text}"))
        else:
            # Default to like, assuming the user might have provided wildcards or its a raw like op
            return query.where(column.like(text))

    def _apply_concept_set_selection(self, query, column, selection):
        """
        Helper to apply ConceptSetSelection filters (inclusion or exclusion).

        Args:
            query: The current SQLAlchemy Select query.
            column: The SQLAlchemy Column object to filter on.
            selection: The ConceptSetSelection object containing codeset_id and is_exclusion.
        """
        if selection is None or selection.codeset_id is None:
            return query

        concept_ids = self._resolve_codeset(selection.codeset_id)

        if selection.is_exclusion:
            # Exclusion: column NOT IN (...)
            if not concept_ids:
                # Exclude nothing -> Include everything (no-op)
                return query
            return query.where(column.notin_(concept_ids))
        else:
            # Inclusion: column IN (...)
            if not concept_ids:
                # Include nothing -> Exclude everything (1 != 1)
                from sqlalchemy import literal

                return query.where(literal(False))
            return query.where(column.in_(concept_ids))
