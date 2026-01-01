from __future__ import annotations

from functools import singledispatchmethod

from sqlalchemy import select, Select

from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    VisitOccurrence,
    ProcedureOccurrence,
    Measurement,
    Observation,
    DeviceExposure,
    Death,
    Specimen,
    Criteria,
)
from omop_cohort_builder.schema import (
    condition_occurrence,
    drug_exposure,
    visit_occurrence,
    procedure_occurrence,
    measurement,
    observation,
    device_exposure,
    death,
    specimen,
)


class QueryBuilder:
    """
    Builds SQL queries from Circe criteria models.
    """

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

        # 1. Condition Type (List of Concepts) -> condition_type_concept_id IN (...)
        if criteria.condition_type:
            concept_ids = [c.concept_id for c in criteria.condition_type]
            query = query.where(
                condition_occurrence.c.condition_type_concept_id.in_(concept_ids)
            )

        # 2. Condition Source Concept -> condition_source_concept_id = ...
        if criteria.condition_source_concept is not None:
            query = query.where(
                condition_occurrence.c.condition_source_concept_id
                == criteria.condition_source_concept
            )

        # 3. Stop Reason (TextFilter)
        if criteria.stop_reason:
            query = self._apply_text_filter(
                query, condition_occurrence.c.stop_reason, criteria.stop_reason
            )

        # 4. Condition Status (List of Concepts)
        if criteria.condition_status:
            concept_ids = [c.concept_id for c in criteria.condition_status]
            query = query.where(
                condition_occurrence.c.condition_status_concept_id.in_(concept_ids)
            )

        return query

    @build_criteria.register
    def _build_specimen(self, criteria: Specimen) -> Select:
        """
        Builds a SQL query for Specimen criteria.
        """
        query = select(specimen)

        # 1. Specimen Type (List of Concepts) -> specimen_type_concept_id IN (...)
        if criteria.specimen_type:
            concept_ids = [c.concept_id for c in criteria.specimen_type]
            query = query.where(specimen.c.specimen_type_concept_id.in_(concept_ids))

        # 2. Quantity (NumericRange)
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, specimen.c.quantity, criteria.quantity
            )

        # 3. Unit (List of Concepts) -> unit_concept_id IN (...)
        if criteria.unit:
            concept_ids = [c.concept_id for c in criteria.unit]
            query = query.where(specimen.c.unit_concept_id.in_(concept_ids))

        # 4. Anatomic Site (List of Concepts) -> anatomic_site_concept_id IN (...)
        if criteria.anatomic_site:
            concept_ids = [c.concept_id for c in criteria.anatomic_site]
            query = query.where(specimen.c.anatomic_site_concept_id.in_(concept_ids))

        # 5. Disease Status (List of Concepts) -> disease_status_concept_id IN (...)
        if criteria.disease_status:
            concept_ids = [c.concept_id for c in criteria.disease_status]
            query = query.where(specimen.c.disease_status_concept_id.in_(concept_ids))

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

        # 1. Device Type (List of Concepts) -> device_type_concept_id IN (...)
        if criteria.device_type:
            concept_ids = [c.concept_id for c in criteria.device_type]
            query = query.where(
                device_exposure.c.device_type_concept_id.in_(concept_ids)
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
        if criteria.device_source_concept is not None:
            query = query.where(
                device_exposure.c.device_source_concept_id
                == criteria.device_source_concept
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

        # 1. Observation Type (List of Concepts)
        if criteria.observation_type:
            concept_ids = [c.concept_id for c in criteria.observation_type]
            query = query.where(
                observation.c.observation_type_concept_id.in_(concept_ids)
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
        if criteria.value_as_concept:
            concept_ids = [c.concept_id for c in criteria.value_as_concept]
            query = query.where(observation.c.value_as_concept_id.in_(concept_ids))

        # 5. Qualifier (List of Concepts)
        if criteria.qualifier:
            concept_ids = [c.concept_id for c in criteria.qualifier]
            query = query.where(observation.c.qualifier_concept_id.in_(concept_ids))

        # 6. Unit (List of Concepts)
        if criteria.unit:
            concept_ids = [c.concept_id for c in criteria.unit]
            query = query.where(observation.c.unit_concept_id.in_(concept_ids))

        # 7. Observation Source Concept (int)
        if criteria.observation_source_concept is not None:
            query = query.where(
                observation.c.observation_source_concept_id
                == criteria.observation_source_concept
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

        # 1. Measurement Type (List of Concepts) -> measurement_type_concept_id IN (...)
        if criteria.measurement_type:
            concept_ids = [c.concept_id for c in criteria.measurement_type]
            query = query.where(
                measurement.c.measurement_type_concept_id.in_(concept_ids)
            )

        # 2. Operator (List of Concepts) -> operator_concept_id IN (...)
        if criteria.operator:
            concept_ids = [c.concept_id for c in criteria.operator]
            query = query.where(measurement.c.operator_concept_id.in_(concept_ids))

        # 3. Value As Number (NumericRange)
        if criteria.value_as_number:
            query = self._apply_numeric_filter(
                query, measurement.c.value_as_number, criteria.value_as_number
            )

        # 4. Value As Concept (List of Concepts) -> value_as_concept_id IN (...)
        if criteria.value_as_concept:
            concept_ids = [c.concept_id for c in criteria.value_as_concept]
            query = query.where(measurement.c.value_as_concept_id.in_(concept_ids))

        # 5. Unit (List of Concepts) -> unit_concept_id IN (...)
        if criteria.unit:
            concept_ids = [c.concept_id for c in criteria.unit]
            query = query.where(measurement.c.unit_concept_id.in_(concept_ids))

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
        if criteria.measurement_source_concept is not None:
            query = query.where(
                measurement.c.measurement_source_concept_id
                == criteria.measurement_source_concept
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

        # 1. Death Type (List of Concepts) -> death_type_concept_id IN (...)
        if criteria.death_type:
            concept_ids = [c.concept_id for c in criteria.death_type]
            query = query.where(death.c.death_type_concept_id.in_(concept_ids))

        # 2. Death Source Concept (int) -> cause_source_concept_id = ...
        if criteria.death_source_concept is not None:
            query = query.where(
                death.c.cause_source_concept_id == criteria.death_source_concept
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

        # 1. Drug Type (List of Concepts) -> drug_type_concept_id IN (...)
        if criteria.drug_type:
            concept_ids = [c.concept_id for c in criteria.drug_type]
            query = query.where(drug_exposure.c.drug_type_concept_id.in_(concept_ids))

        # TODO: Implement drug_type_cs (ConceptSet)

        # 2. Stop Reason (TextFilter) -> stop_reason LIKE ...
        if criteria.stop_reason:
            query = self._apply_text_filter(
                query, drug_exposure.c.stop_reason, criteria.stop_reason
            )

        # 3. Refills (NumericRange) -> refills op value
        if criteria.refills:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.refills, criteria.refills
            )

        # 4. Quantity (NumericRange) -> quantity op value
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.quantity, criteria.quantity
            )

        # 5. Days Supply (NumericRange) -> days_supply op value
        if criteria.days_supply:
            query = self._apply_numeric_filter(
                query, drug_exposure.c.days_supply, criteria.days_supply
            )

        # 6. Route Concept (List of Concepts) -> route_concept_id IN (...)
        if criteria.route_concept:
            concept_ids = [c.concept_id for c in criteria.route_concept]
            query = query.where(drug_exposure.c.route_concept_id.in_(concept_ids))

        # TODO: Implement route_concept_cs

        # 7. Lot Number (TextFilter) -> lot_number LIKE ...
        if criteria.lot_number:
            query = self._apply_text_filter(
                query, drug_exposure.c.lot_number, criteria.lot_number
            )

        # 8. Drug Source Concept (int) -> drug_source_concept_id = ...
        if criteria.drug_source_concept is not None:
            query = query.where(
                drug_exposure.c.drug_source_concept_id == criteria.drug_source_concept
            )

        # 9. Dose Unit (List of Concepts)
        # TODO: Implement dose_unit.
        # This requires joining to DRUG_STRENGTH or DOSE_ERA which is not yet supported in this atomic unit.
        # The drug_exposure table in standard OMOP CDM does not have dose_unit_concept_id.
        if criteria.dose_unit:
            pass

        return query

    @build_criteria.register
    def _build_visit_occurrence(self, criteria: VisitOccurrence) -> Select:
        """
        Builds a SQL query for VisitOccurrence criteria.
        """
        query = select(visit_occurrence)

        # 1. Visit Type (List of Concepts) -> visit_type_concept_id IN (...)
        if criteria.visit_type:
            concept_ids = [c.concept_id for c in criteria.visit_type]
            query = query.where(
                visit_occurrence.c.visit_type_concept_id.in_(concept_ids)
            )

        # 2. Visit Source Concept -> visit_source_concept_id = ...
        if criteria.visit_source_concept is not None:
            query = query.where(
                visit_occurrence.c.visit_source_concept_id
                == criteria.visit_source_concept
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

        # 1. Procedure Type (List of Concepts) -> procedure_type_concept_id IN (...)
        if criteria.procedure_type:
            concept_ids = [c.concept_id for c in criteria.procedure_type]
            query = query.where(
                procedure_occurrence.c.procedure_type_concept_id.in_(concept_ids)
            )

        # 2. Modifier (List of Concepts) -> modifier_concept_id IN (...)
        if criteria.modifier:
            concept_ids = [c.concept_id for c in criteria.modifier]
            query = query.where(
                procedure_occurrence.c.modifier_concept_id.in_(concept_ids)
            )

        # 3. Quantity (NumericRange) -> quantity op value
        if criteria.quantity:
            query = self._apply_numeric_filter(
                query, procedure_occurrence.c.quantity, criteria.quantity
            )

        # 4. Procedure Source Concept -> procedure_source_concept_id = ...
        if criteria.procedure_source_concept is not None:
            query = query.where(
                procedure_occurrence.c.procedure_source_concept_id
                == criteria.procedure_source_concept
            )

        # 5. Occurrence Start Date -> procedure_date
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query,
                procedure_occurrence.c.procedure_date,
                criteria.occurrence_start_date,
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
