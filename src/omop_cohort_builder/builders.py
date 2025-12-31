from __future__ import annotations

from typing import Any, cast

from sqlalchemy import select, Select

from omop_cohort_builder.domain import ConditionOccurrence
from omop_cohort_builder.schema import condition_occurrence


class QueryBuilder:
    """
    Builds SQL queries from Circe criteria objects using SQLAlchemy Core.
    """

    def build_condition_occurrence(self, criteria: ConditionOccurrence) -> Select:
        """
        Builds a SQLAlchemy Select statement for a ConditionOccurrence criteria.
        """
        # Start with a basic SELECT * FROM condition_occurrence
        # casting to Select[Any] to avoid mypy strictness issues with SQLAlchemy generic types for now
        query = cast(Select[Any], select(condition_occurrence))

        # In the future, we will add WHERE clauses based on the criteria fields
        # (e.g. codeset_id, occurrence_start_date, etc.)

        return query
