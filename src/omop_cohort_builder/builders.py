from __future__ import annotations

from functools import singledispatchmethod

from sqlalchemy import select, Select

from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    VisitOccurrence,
    Criteria,
)
from omop_cohort_builder.schema import (
    condition_occurrence,
    drug_exposure,
    visit_occurrence,
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
