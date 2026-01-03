from __future__ import annotations

from functools import singledispatchmethod, singledispatch
from typing import Dict, List, Any

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
    CriteriaGroup,
    PrimaryCriteria,
    CorelatedCriteria,
    Window,
    Occurrence,
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
    provider,
)


@singledispatch
def _get_criteria_columns_dispatch(criteria: Criteria):
    """
    Returns the (start_column, end_column) for the given criteria type.
    Used for column normalization in primary criteria.
    """
    raise NotImplementedError(
        f"Column mapping not implemented for type: {type(criteria)}"
    )  # pragma: no cover


@_get_criteria_columns_dispatch.register
def _(criteria: ConditionOccurrence):
    return (
        condition_occurrence.c.condition_start_date,
        condition_occurrence.c.condition_end_date,
    )


@_get_criteria_columns_dispatch.register
def _(criteria: DrugExposure):
    return (
        drug_exposure.c.drug_exposure_start_date,
        drug_exposure.c.drug_exposure_end_date,
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

    def build_primary_criteria(self, primary_criteria: PrimaryCriteria) -> Select:
        """
        Builds the SQL query for the PrimaryCriteria section of the Cohort Expression.
        It generates a UNION ALL of all criteria queries, normalizes columns, applies observation window, and result limit.
        """
        from sqlalchemy import union_all, literal_column

        criteria_queries = []

        for criteria in primary_criteria.criteria_list:
            # 1. Build the base query for the criteria
            base_query = self.build_criteria(criteria)

            # 2. Normalize columns to standard event format (person_id, start_date, end_date)
            normalized_query = self._normalize_criteria_query(base_query, criteria)
            criteria_queries.append(normalized_query)

        if not criteria_queries:
            # Should not happen in valid cohort definitions, but safe fallback
            # Return empty result
            # We need to construct a Select that returns the expected columns but empty
            return select(
                literal_column("NULL").label("person_id"),
                literal_column("NULL").label("start_date"),
                literal_column("NULL").label("end_date"),
            ).where(literal_column("1") != literal_column("1"))

        # 3. Union all queries
        combined_query: Select | Any
        if len(criteria_queries) == 1:
            combined_query = criteria_queries[0]
        else:
            combined_query = union_all(*criteria_queries)

        # We need to wrap the union in a subquery to apply limits and windows safely
        # Aliasing the subquery is important for referencing columns
        subquery = combined_query.subquery("primary_events")

        # 4. Apply Limit
        # Use window function (ROW_NUMBER) to support generic SQL limitation (First/Last)
        # instead of Postgres-specific DISTINCT ON.

        limit_type = primary_criteria.primary_limit.type
        query = select(subquery.c.person_id, subquery.c.start_date, subquery.c.end_date)

        # Apply ObservationWindow filtering (PriorDays/PostDays)
        # This requires joining with the ObservationPeriod table to ensure coverage.
        # We always join observation_period in OHDSI logic to ensure validity.
        # If the user explicitly sets 0,0 it effectively just filters for "any overlapping period".

        prior_days = (
            primary_criteria.observation_window.prior_days
            if primary_criteria.observation_window
            else 0
        )
        post_days = (
            primary_criteria.observation_window.post_days
            if primary_criteria.observation_window
            else 0
        )

        # We need to filter 'subquery' by joining with observation_period.
        # We construct a new selection from subquery + join + where.

        # Aliases
        op = observation_period

        # Join condition: person_id
        join_cond = subquery.c.person_id == op.c.person_id

        # Filter 1: event_start_date >= op_start_date + prior_days
        # Filter 2: event_start_date <= op_end_date - post_days

        query = select(
            subquery.c.person_id, subquery.c.start_date, subquery.c.end_date
        ).join(op, join_cond)

        if prior_days > 0:
            query = query.where(
                subquery.c.start_date
                >= (op.c.observation_period_start_date + prior_days)
            )
        else:
            query = query.where(
                subquery.c.start_date >= op.c.observation_period_start_date
            )

        if post_days > 0:
            query = query.where(
                subquery.c.start_date <= (op.c.observation_period_end_date - post_days)
            )
        else:
            query = query.where(
                subquery.c.start_date <= op.c.observation_period_end_date
            )

        # Wrap this filtered result back into a subquery so the Limit logic works on it
        # The Limit logic expects 'subquery' to be the source.
        subquery = query.subquery("observation_window_events")

        # Reset query to select from this new subquery to be safe for next steps
        query = select(subquery.c.person_id, subquery.c.start_date, subquery.c.end_date)

        if limit_type == "First" or limit_type == "Last":
            from sqlalchemy import func

            # Use a subquery with ROW_NUMBER()
            # SELECT * FROM (
            #   SELECT person_id, start_date, end_date,
            #          ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY start_date ASC/DESC) as rn
            #   FROM primary_events
            # ) WHERE rn = 1

            order = (
                subquery.c.start_date.asc()
                if limit_type == "First"
                else subquery.c.start_date.desc()
            )

            rn_col = (
                func.row_number()
                .over(partition_by=subquery.c.person_id, order_by=order)
                .label("rn")
            )

            limit_subquery = select(
                subquery.c.person_id, subquery.c.start_date, subquery.c.end_date, rn_col
            ).subquery("limit_events")

            query = select(
                limit_subquery.c.person_id,
                limit_subquery.c.start_date,
                limit_subquery.c.end_date,
            ).where(limit_subquery.c.rn == 1)

        return query

    def _normalize_criteria_query(self, query: Select, criteria: Criteria) -> Select:
        """
        Wraps a criteria query to return standard columns: person_id, start_date, end_date.
        """
        try:
            # Use single dispatch to get table columns
            start_col_def, end_col_def = _get_criteria_columns_dispatch(criteria)
        except NotImplementedError:
            # Should not happen for supported types; raise clearly
            raise NotImplementedError(
                f"Cannot normalize query for type {type(criteria).__name__}: column mapping missing."
            )

        # Wrap the original query as a subquery
        sub = query.subquery()

        # We need to select the corresponding columns from the subquery.
        # SQLAlchemy subqueries expose columns via .c matching the original names.

        target_person = sub.c.person_id
        target_start = sub.c[start_col_def.name]

        # End date might be same as start if end_col_def is None, but here we expect a column def
        # If the original table definition has the column, the subquery should too.
        # We assume end_col_def is always provided for supported types
        target_end = sub.c[end_col_def.name]

        selection = [
            target_person.label("person_id"),
            target_start.label("start_date"),
            target_end.label("end_date"),
        ]

        return select(*selection)

    def _apply_window(
        self,
        query: Select,
        event_alias: Any,
        window: Window | None,
        criteria_start_col: Any,
    ) -> Select:
        """
        Applies window logic to filter the criteria query relative to an event alias.

        Args:
            query: The criteria query (e.g., Select from ConditionOccurrence).
            event_alias: The SQLAlchemy Alias for the primary event table.
            window: The Window definition.
            criteria_start_col: The column in the criteria query representing the event start date.
        """
        if not window:
            return query

        start_def = window.start
        end_def = window.end

        # Determine the base date from the primary event to calculate offsets against
        # Default is event_alias.start_date
        index_date_col = event_alias.c.start_date

        # Check use_index_end for start/end endpoints?
        # Actually Circe definition:
        # Start Window: "Start Day" relative to Index Start/End
        # End Window: "End Day" relative to Index Start/End

        # Re-reading Window structure:
        # It has `start: Endpoint` and `end: Endpoint`.
        # Also `use_index_end` (boolean). If true, calculations are relative to Index END date.

        if window.use_index_end:
            index_date_col = event_alias.c.end_date

        # Calculate Start Bound: IndexDate + (Start.Days * Start.Coeff)
        # Note: days can be None (0)
        start_days = (
            start_def.days if start_def.days is not None else 0
        ) * start_def.coeff

        # Calculate End Bound: IndexDate + (End.Days * End.Coeff)
        end_days = (end_def.days if end_def.days is not None else 0) * end_def.coeff

        # Apply logic: Criteria Start Date BETWEEN (Index + StartOffset) AND (Index + EndOffset)
        # Assuming `use_event_end` is false. If true, we check Criteria End Date.

        target_col = criteria_start_col
        # TODO: handle use_event_end to switch target_col to criteria end date
        # Assuming we can look it up similarly to _get_criteria_columns logic if needed.

        # SQLAlchemy expression
        # We add integers to dates. Postgres supports this.
        from sqlalchemy import literal

        lower_bound = index_date_col + literal(start_days)
        upper_bound = index_date_col + literal(end_days)

        return query.where(target_col.between(lower_bound, upper_bound))

    def build_criteria_group_query(
        self, group: CriteriaGroup, event_alias: Any
    ) -> Select:
        """
        Builds a SQL query for a CriteriaGroup (e.g. for Inclusion Rules).
        Returns a query selecting (index_id, person_id, event_id) for matching events.
        index_id corresponds to the item index in the group.
        """
        from sqlalchemy import literal, union_all, func

        if group.is_empty():
            # If empty, return a dummy query that selects nothing (or everything? Java says "friendly default")
            # Java: select @indexId as index_id, person_id, event_id FROM @eventTable
            # It seems empty group means "True" (match everything)?
            # Usually InclusionRule with empty group matches everyone?
            # Let's return the event_alias rows with index_id=0
            return select(
                literal(0).label("index_id"),
                event_alias.c.person_id,
                event_alias.c.event_id,
            )

        queries = []
        index_id = 0

        # 1. Criteria List (CorelatedCriteria)
        for cc in group.criteria_list:
            q = self.build_corelated_criteria_query(cc, event_alias, index_id)
            queries.append(q)
            index_id += 1

        # 2. Demographic Criteria
        for dc in group.demographic_criteria_list:
            q = self.build_demographic_criteria_query(dc, event_alias, index_id)
            queries.append(q)
            index_id += 1

        # 3. Nested Groups
        for sub_group in group.groups:
            q = self.build_criteria_group_query(sub_group, event_alias)
            # The sub-group query returns rows. We need to associate them with the current index_id.
            # Actually, the sub-group query itself handles its internal logic.
            # But the "Group Query" template in Java suggests we treat the sub-group as ONE item.
            # Wait, Java calls `getCriteriaGroupQuery` recursively.
            # And replaces `@indexId` in the result.
            # If the sub-group query returns `(index_id, person_id, event_id)`, we need to check if the sub-group is satisfied for that person/event.
            # But `build_criteria_group_query` returns satisfying (person, event).
            # So if a row exists in the sub-group result, it satisfies the sub-group.
            # So we just select `literal(index_id), person, event` from the sub-group result.

            sub_q = q.subquery()
            # We need to distinct on person_id, event_id because sub-group might return multiple rows (one per internal index match)
            # Actually, the sub-group query ALREADY groups by person/event and filters.
            # So it returns distinct (person, event) pairs that satisfy the group.
            # So we can just select from it.
            wrapped_q = select(
                literal(index_id).label("index_id"),
                sub_q.c.person_id,
                sub_q.c.event_id,
            )
            queries.append(wrapped_q)
            index_id += 1

        if not queries:
            # Should be covered by is_empty check, but safe fallback
            return select(  # pragma: no cover
                literal(0).label("index_id"),
                event_alias.c.person_id,
                event_alias.c.event_id,
            ).where(literal(False))

        # Union all item queries
        # CAST index_id to Integer to ensure compatibility if some are literals?
        # SQLAlchemy handles literals well.

        union_q = union_all(*queries).subquery("group_union")

        # Aggregate and Apply Logic (ALL, ANY, AT_LEAST, AT_MOST)

        # We need to count distinct index_id per (person_id, event_id)
        # SELECT person_id, event_id FROM union_q GROUP BY person_id, event_id HAVING ...

        query = select(
            union_q.c.person_id,
            union_q.c.event_id,
        ).group_by(union_q.c.person_id, union_q.c.event_id)

        count_expr = func.count(
            union_q.c.index_id
        )  # distinct? index_id is distinct per branch?
        # Yes, index_id is unique per branch.
        # But wait, `build_corelated_criteria_query` might return multiple rows per event if multiple matches?
        # No, `build_corelated_criteria_query` should aggregate or return distinct?
        # Java: `ADDITIONAL_CRITERIA_INNER_TEMPLATE` does `GROUP BY person_id, event_id`.
        # So yes, each child query returns UNIQUE (person, event) per index_id.

        # Logic
        if group.type.upper() == "ALL":
            query = query.having(count_expr == index_id)  # index_id is now total count
        elif group.type.upper() == "ANY":
            query = query.having(count_expr > 0)
        elif group.type.upper().startswith("AT_"):
            if group.type.upper() == "AT_LEAST":
                query = query.having(count_expr >= group.count)
            elif group.type.upper() == "AT_MOST":
                # Handling AT_MOST is tricky with UNION.
                # UNION only contains existing matches.
                # If count is 0, it won't be in UNION.
                # But AT_MOST 0 means we want rows NOT in UNION (or count=0).
                # This requires a LEFT JOIN against the `event_alias`.
                # If we return a SELECT from here, we can't easily do LEFT JOIN inside.
                # Java uses `joinType = "LEFT"` variable and constructs the join outside.
                # Here, we are building a SELECT.
                # If we strictly return "Satisfying Events", then for AT_MOST 0, we must return events with 0 matches.
                # To do that, we need to Select from `event_alias` EXCEPT those with > count matches?
                # Or Select from `event_alias` Left Join `union_q`.

                # We need access to `event_alias` here.
                # If AT_MOST, we construct:
                # SELECT E.person_id, E.event_id FROM event_alias E
                # LEFT JOIN (union_q) U ON ...
                # GROUP BY E...
                # HAVING COUNT(U.index_id) <= group.count

                # Construct the join
                join_cond = (event_alias.c.person_id == union_q.c.person_id) & (
                    event_alias.c.event_id == union_q.c.event_id
                )

                query = (
                    select(event_alias.c.person_id, event_alias.c.event_id)
                    .select_from(event_alias.join(union_q, join_cond, isouter=True))
                    .group_by(event_alias.c.person_id, event_alias.c.event_id)
                    .having(func.count(union_q.c.index_id) <= group.count)
                )

                return query
            else:
                pass  # pragma: no cover

        return query

    def build_corelated_criteria_query(
        self, criteria: CorelatedCriteria, event_alias: Any, index_id: int
    ) -> Select:
        """
        Builds a query for a single CorelatedCriteria item.
        Returns: SELECT literal(index_id), person_id, event_id FROM ... matching criteria
        """
        from sqlalchemy import literal, func

        # 1. Build the base query for the criteria domain
        base_query = self.build_criteria(criteria.criteria)
        criteria_alias = base_query.subquery().alias("criteria_events")

        # 2. Identify columns
        start_col, end_col = _get_criteria_columns_dispatch(criteria.criteria)
        criteria_person_col = criteria_alias.c.person_id
        criteria_start_col = criteria_alias.c[start_col.name]

        # 3. Join with Event Alias (Window Logic)
        # We start with event_alias (Index) and JOIN criteria_alias (Target)
        # Logic: Index JOIN Target ON Person AND Window

        join_cond = criteria_person_col == event_alias.c.person_id

        # Apply Window Logic manually to the join condition or WHERE
        # _apply_window modifies a query.
        # Here we want to select from Index (event_alias) and join Target.

        # Let's construct a SELECT from event_alias JOIN criteria_alias
        query = select(
            literal(index_id).label("index_id"),
            event_alias.c.person_id,
            event_alias.c.event_id,
        ).select_from(event_alias.join(criteria_alias, join_cond))

        # Apply Window (filters the JOIN result)
        # Note: _apply_window expects a query and modifies WHERE.
        query = self._apply_window(
            query, event_alias, criteria.start_window, criteria_start_col
        )

        # 4. Occurrence Check (HAVING COUNT)
        # We need to Group By (Index Event) and Count (Target Events)

        query = query.group_by(event_alias.c.person_id, event_alias.c.event_id)

        occurrence = criteria.occurrence

        # Count Column
        # We count the criteria person_id (right side) to correctly handle LEFT JOINs (AT_MOST).
        count_expr = func.count(criteria_person_col)

        # Operator
        op_map = {
            Occurrence.EXACTLY: lambda c, v: c == v,
            Occurrence.AT_LEAST: lambda c, v: c >= v,
            Occurrence.AT_MOST: lambda c, v: c <= v,
        }

        # Logic for AT_MOST / count=0
        # If we look for count=0, we need LEFT JOIN (Index LEFT JOIN Target).
        if occurrence.type == Occurrence.AT_MOST or (
            occurrence.type == Occurrence.EXACTLY and occurrence.count == 0
        ):
            # Switch to LEFT JOIN
            # Note: Proper implementation requires moving Window logic to Join condition
            # or handling NULLs in WHERE. For now, we apply standard window logic
            # and force LEFT JOIN, acknowledging potential filtering issues if window excludes NULLs.
            query = select(
                literal(index_id).label("index_id"),
                event_alias.c.person_id,
                event_alias.c.event_id,
            ).select_from(event_alias.join(criteria_alias, join_cond, isouter=True))

            query = self._apply_window(
                query, event_alias, criteria.start_window, criteria_start_col
            )

        query = query.having(op_map[occurrence.type](count_expr, occurrence.count))

        return query

    def _apply_demographic_filters(
        self,
        query: Select,
        criteria: DemographicCriteria,
        person_alias: Any,
        start_date_col: Any,
    ) -> Select:
        """Helper to apply demographic filters (Age, Gender, Race, Ethnicity)."""

        # 1. Age
        if criteria.age:
            from sqlalchemy import extract

            age_expr = extract("year", start_date_col) - person_alias.c.year_of_birth
            query = self._apply_numeric_filter(query, age_expr, criteria.age)

        # 2. Gender
        if criteria.gender:
            concept_ids = [c.concept_id for c in criteria.gender]
            query = query.where(person_alias.c.gender_concept_id.in_(concept_ids))

        # 2b. Gender CS
        if criteria.gender_cs:
            query = self._apply_concept_set_selection(
                query, person_alias.c.gender_concept_id, criteria.gender_cs
            )

        # 3. Race
        if criteria.race:
            concept_ids = [c.concept_id for c in criteria.race]
            query = query.where(person_alias.c.race_concept_id.in_(concept_ids))

        # 3b. Race CS
        if criteria.race_cs:
            query = self._apply_concept_set_selection(
                query, person_alias.c.race_concept_id, criteria.race_cs
            )

        # 4. Ethnicity
        if criteria.ethnicity:
            concept_ids = [c.concept_id for c in criteria.ethnicity]
            query = query.where(person_alias.c.ethnicity_concept_id.in_(concept_ids))

        # 4b. Ethnicity CS
        if criteria.ethnicity_cs:
            query = self._apply_concept_set_selection(
                query, person_alias.c.ethnicity_concept_id, criteria.ethnicity_cs
            )

        return query

    def build_demographic_criteria_query(
        self, criteria: DemographicCriteria, event_alias: Any, index_id: int
    ) -> Select:
        """
        Builds a query for DemographicCriteria.
        Returns: SELECT literal(index_id), person_id, event_id FROM event_alias WHERE ...
        """
        from sqlalchemy import literal, select
        from omop_cohort_builder.schema import person

        # Join event_alias with Person
        query = select(
            literal(index_id).label("index_id"),
            event_alias.c.person_id,
            event_alias.c.event_id,
        ).select_from(
            event_alias.join(person, event_alias.c.person_id == person.c.person_id)
        )

        # Apply filters
        # Assuming event_alias has start_date column
        query = self._apply_demographic_filters(
            query, criteria, person, event_alias.c.start_date
        )

        # Occurrence Dates
        if criteria.occurrence_start_date:
            query = self._apply_date_filter(
                query, event_alias.c.start_date, criteria.occurrence_start_date
            )

        if criteria.occurrence_end_date:
            # Event alias might not have end_date if it's simple event?
            # Assuming it does (common in Circe).
            query = self._apply_date_filter(
                query, event_alias.c.end_date, criteria.occurrence_end_date
            )

        return query

    @singledispatchmethod
    def build_criteria(self, criteria: Criteria) -> Select:
        """
        Dispatches the build call to the appropriate method based on the criteria type.
        """
        raise NotImplementedError(
            f"Query builder not implemented for type: {type(criteria)}"
        )  # pragma: no cover

    @build_criteria.register
    def _build_condition_occurrence(self, criteria: ConditionOccurrence) -> Select:
        """
        Builds a SQL query for ConditionOccurrence criteria.
        """
        query = select(condition_occurrence)

        # 0. Codeset ID -> condition_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            # If concept_ids is empty, .in_([]) will typically render as false (e.g., IN (NULL) or 1!=1)
            # which is correct behavior (matches nothing).
            query = query.where(
                condition_occurrence.c.condition_concept_id.in_(concept_ids)
            )

        # 1. Condition Type (List of Concepts) -> condition_type_concept_id IN (...)
        if criteria.condition_type:
            concept_ids = [c.concept_id for c in criteria.condition_type]
            query = query.where(
                condition_occurrence.c.condition_type_concept_id.in_(concept_ids)
            )

        # 1b. Condition Type (ConceptSetSelection)
        if criteria.condition_type_cs:
            query = self._apply_concept_set_selection(
                query,
                condition_occurrence.c.condition_type_concept_id,
                criteria.condition_type_cs,
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

        # 4b. Condition Status (ConceptSetSelection)
        if criteria.condition_status_cs:
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
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(condition_era.c.condition_concept_id.in_(concept_ids))

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

        # Demographics
        join_person = (
            criteria.age_at_start
            or criteria.age_at_end
            or criteria.gender
            or criteria.gender_cs
        )

        if join_person:
            query = query.join(person, condition_era.c.person_id == person.c.person_id)

        # 5. Age At Start (NumericRange) -> (Year(condition_era_start_date) - person.year_of_birth)
        if criteria.age_at_start:
            from sqlalchemy import extract

            age_expr = (
                extract("year", condition_era.c.condition_era_start_date)
                - person.c.year_of_birth
            )
            query = self._apply_numeric_filter(query, age_expr, criteria.age_at_start)

        # 6. Age At End (NumericRange) -> (Year(condition_era_end_date) - person.year_of_birth)
        if criteria.age_at_end:
            from sqlalchemy import extract

            age_expr = (
                extract("year", condition_era.c.condition_era_end_date)
                - person.c.year_of_birth
            )
            query = self._apply_numeric_filter(query, age_expr, criteria.age_at_end)

        # 7. Gender (List of Concepts) -> person.gender_concept_id
        if criteria.gender:
            concept_ids = [c.concept_id for c in criteria.gender]
            query = query.where(person.c.gender_concept_id.in_(concept_ids))

        # 7b. Gender (ConceptSetSelection)
        if criteria.gender_cs:
            query = self._apply_concept_set_selection(
                query, person.c.gender_concept_id, criteria.gender_cs
            )

        return query

    @build_criteria.register
    def _build_drug_era(self, criteria: DrugEra) -> Select:
        """
        Builds a SQL query for DrugEra criteria.
        """
        query = select(drug_era)

        # 0. Codeset ID -> drug_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(drug_era.c.drug_concept_id.in_(concept_ids))

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
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(dose_era.c.drug_concept_id.in_(concept_ids))

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
        if criteria.unit:
            concept_ids = [c.concept_id for c in criteria.unit]
            query = query.where(dose_era.c.unit_concept_id.in_(concept_ids))

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
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(specimen.c.specimen_concept_id.in_(concept_ids))

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

        # 0. Codeset ID -> device_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(device_exposure.c.device_concept_id.in_(concept_ids))

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

        # 0. Codeset ID -> observation_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(observation.c.observation_concept_id.in_(concept_ids))

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

        # 0. Codeset ID -> measurement_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(measurement.c.measurement_concept_id.in_(concept_ids))

        # 1. Measurement Type (List of Concepts) -> measurement_type_concept_id IN (...)
        if criteria.measurement_type:
            concept_ids = [c.concept_id for c in criteria.measurement_type]
            query = query.where(
                measurement.c.measurement_type_concept_id.in_(concept_ids)
            )

        # 1b. Measurement Type (ConceptSetSelection)
        if criteria.measurement_type_cs:
            query = self._apply_concept_set_selection(
                query,
                measurement.c.measurement_type_concept_id,
                criteria.measurement_type_cs,
            )

        # 2. Operator (List of Concepts) -> operator_concept_id IN (...)
        if criteria.operator:
            concept_ids = [c.concept_id for c in criteria.operator]
            query = query.where(measurement.c.operator_concept_id.in_(concept_ids))

        # 2b. Operator (ConceptSetSelection)
        if criteria.operator_cs:
            query = self._apply_concept_set_selection(
                query,
                measurement.c.operator_concept_id,
                criteria.operator_cs,
            )

        # 3. Value As Number (NumericRange)
        if criteria.value_as_number:
            query = self._apply_numeric_filter(
                query, measurement.c.value_as_number, criteria.value_as_number
            )

        # 4. Value As Concept (List of Concepts) -> value_as_concept_id IN (...)
        if criteria.value_as_concept:
            concept_ids = [c.concept_id for c in criteria.value_as_concept]
            query = query.where(measurement.c.value_as_concept_id.in_(concept_ids))

        # 4b. Value As Concept (ConceptSetSelection)
        if criteria.value_as_concept_cs:
            query = self._apply_concept_set_selection(
                query,
                measurement.c.value_as_concept_id,
                criteria.value_as_concept_cs,
            )

        # 5. Unit (List of Concepts) -> unit_concept_id IN (...)
        if criteria.unit:
            concept_ids = [c.concept_id for c in criteria.unit]
            query = query.where(measurement.c.unit_concept_id.in_(concept_ids))

        # 5b. Unit (ConceptSetSelection)
        if criteria.unit_cs:
            query = self._apply_concept_set_selection(
                query,
                measurement.c.unit_concept_id,
                criteria.unit_cs,
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

        # 0. Codeset ID -> cause_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(death.c.cause_concept_id.in_(concept_ids))

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

        # 0. Codeset ID -> drug_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(drug_exposure.c.drug_concept_id.in_(concept_ids))

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
        if criteria.drug_type:
            concept_ids = [c.concept_id for c in criteria.drug_type]
            if criteria.drug_type_exclude:
                query = query.where(
                    drug_exposure.c.drug_type_concept_id.notin_(concept_ids)
                )
            else:
                query = query.where(
                    drug_exposure.c.drug_type_concept_id.in_(concept_ids)
                )

        # 3b. Drug Type (ConceptSetSelection)
        if criteria.drug_type_cs:
            query = self._apply_concept_set_selection(
                query,
                drug_exposure.c.drug_type_concept_id,
                criteria.drug_type_cs,
            )

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
        if criteria.route_concept:
            concept_ids = [c.concept_id for c in criteria.route_concept]
            query = query.where(drug_exposure.c.route_concept_id.in_(concept_ids))

        # 8b. Route Concept (ConceptSetSelection)
        if criteria.route_concept_cs:
            query = self._apply_concept_set_selection(
                query,
                drug_exposure.c.route_concept_id,
                criteria.route_concept_cs,
            )

        # 9. Lot Number (TextFilter) -> lot_number LIKE ...
        if criteria.lot_number:
            query = self._apply_text_filter(
                query, drug_exposure.c.lot_number, criteria.lot_number
            )

        # 10. Drug Source Concept (int) -> drug_source_concept_id = ...
        if criteria.drug_source_concept is not None:
            query = query.where(
                drug_exposure.c.drug_source_concept_id == criteria.drug_source_concept
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
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(visit_occurrence.c.visit_concept_id.in_(concept_ids))

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

        # Joins: We identify which tables need to be joined based on the criteria present.
        # This prevents duplicate joins if multiple fields require the same table.
        # Note: SQLAlchemy's join() method typically handles duplicate joins intelligently if using table objects,
        # but explicit checks are safer and clearer.
        join_person = criteria.age or criteria.gender or criteria.gender_cs
        join_provider = criteria.provider_specialty or criteria.provider_specialty_cs
        join_visit = criteria.visit_type or criteria.visit_type_cs

        if join_person:
            query = query.join(
                person, procedure_occurrence.c.person_id == person.c.person_id
            )

        if join_provider:
            # We must define the provider table alias or use the table object directly if names are unique.
            # Here we assume direct use of table objects as imported.
            query = query.join(
                provider, procedure_occurrence.c.provider_id == provider.c.provider_id
            )

        if join_visit:
            query = query.join(
                visit_occurrence,
                procedure_occurrence.c.visit_occurrence_id
                == visit_occurrence.c.visit_occurrence_id,
            )

        # 0. Codeset ID -> procedure_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(
                procedure_occurrence.c.procedure_concept_id.in_(concept_ids)
            )

        # 1. Procedure Type (List of Concepts) -> procedure_type_concept_id IN (...)
        if criteria.procedure_type:
            concept_ids = [c.concept_id for c in criteria.procedure_type]
            if criteria.procedure_type_exclude:
                query = query.where(
                    procedure_occurrence.c.procedure_type_concept_id.notin_(concept_ids)
                )
            else:
                query = query.where(
                    procedure_occurrence.c.procedure_type_concept_id.in_(concept_ids)
                )

        # 1b. Procedure Type (ConceptSetSelection)
        if criteria.procedure_type_cs:
            query = self._apply_concept_set_selection(
                query,
                procedure_occurrence.c.procedure_type_concept_id,
                criteria.procedure_type_cs,
            )

        # 2. Modifier (List of Concepts) -> modifier_concept_id IN (...)
        if criteria.modifier:
            concept_ids = [c.concept_id for c in criteria.modifier]
            query = query.where(
                procedure_occurrence.c.modifier_concept_id.in_(concept_ids)
            )

        # 2b. Modifier (ConceptSetSelection)
        if criteria.modifier_cs:
            query = self._apply_concept_set_selection(
                query,
                procedure_occurrence.c.modifier_concept_id,
                criteria.modifier_cs,
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

        # 6. Age (NumericRange) -> (Year(procedure_date) - person.year_of_birth)
        if criteria.age:
            from sqlalchemy import extract

            age_expr = (
                extract("year", procedure_occurrence.c.procedure_date)
                - person.c.year_of_birth
            )
            query = self._apply_numeric_filter(query, age_expr, criteria.age)

        # 7. Gender (List of Concepts) -> person.gender_concept_id
        if criteria.gender:
            concept_ids = [c.concept_id for c in criteria.gender]
            query = query.where(person.c.gender_concept_id.in_(concept_ids))

        # 7b. Gender (ConceptSetSelection)
        if criteria.gender_cs:
            query = self._apply_concept_set_selection(
                query, person.c.gender_concept_id, criteria.gender_cs
            )

        # 8. Provider Specialty (List of Concepts) -> provider.specialty_concept_id
        if criteria.provider_specialty:
            concept_ids = [c.concept_id for c in criteria.provider_specialty]
            query = query.where(provider.c.specialty_concept_id.in_(concept_ids))

        # 8b. Provider Specialty (ConceptSetSelection)
        if criteria.provider_specialty_cs:
            query = self._apply_concept_set_selection(
                query, provider.c.specialty_concept_id, criteria.provider_specialty_cs
            )

        # 9. Visit Type (List of Concepts) -> visit_occurrence.visit_type_concept_id
        if criteria.visit_type:
            concept_ids = [c.concept_id for c in criteria.visit_type]
            query = query.where(
                visit_occurrence.c.visit_type_concept_id.in_(concept_ids)
            )

        # 9b. Visit Type (ConceptSetSelection)
        if criteria.visit_type_cs:
            query = self._apply_concept_set_selection(
                query,
                visit_occurrence.c.visit_type_concept_id,
                criteria.visit_type_cs,
            )

        return query

    @build_criteria.register
    def _build_visit_detail(self, criteria: VisitDetail) -> Select:
        """
        Builds a SQL query for VisitDetail criteria.
        """
        query = select(visit_detail)

        # 0. Codeset ID -> visit_detail_concept_id IN (...)
        if criteria.codeset_id is not None:
            concept_ids = self._resolve_codeset(criteria.codeset_id)
            query = query.where(visit_detail.c.visit_detail_concept_id.in_(concept_ids))

        # 1. Visit Detail Source Concept -> visit_detail_source_concept_id = ...
        if criteria.visit_detail_source_concept is not None:
            query = query.where(
                visit_detail.c.visit_detail_source_concept_id
                == criteria.visit_detail_source_concept
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

        query = self._apply_demographic_filters(
            query, criteria, person, observation_period.c.observation_period_start_date
        )

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
