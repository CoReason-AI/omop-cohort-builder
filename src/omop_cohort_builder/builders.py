from __future__ import annotations

from functools import singledispatchmethod

from sqlalchemy import select, Select

from omop_cohort_builder.domain import ConditionOccurrence, Criteria
from omop_cohort_builder.schema import condition_occurrence


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
