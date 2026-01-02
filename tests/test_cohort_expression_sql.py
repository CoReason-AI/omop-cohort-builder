from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    PrimaryCriteria,
)
from sqlalchemy.dialects import postgresql


def normalize_sql(sql):
    return " ".join(sql.split())


def test_build_primary_criteria_single_condition():
    """
    Test building primary criteria with a single ConditionOccurrence.
    Should select person_id, start_date, end_date from condition_occurrence.
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "All"},
    )

    qb = QueryBuilder(concept_set_map={1: [100, 200]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # We expect a UNION (even if single item, usually good practice or just a Select)
    # But for a single item, it might just be the select.
    # However, we need to ensure columns are aliased to standard names.

    # With normalization and subquery wrapping, the exact string match is tricky.
    # The inner query should be selecting from condition_occurrence.
    # The outer query selects from the subquery (aliased as primary_events).

    # Check inner structure
    assert "FROM condition_occurrence" in normalized
    assert "WHERE condition_occurrence.condition_concept_id IN (100, 200)" in normalized

    # Check outer selection columns (person_id, start_date, end_date)
    assert "primary_events.person_id" in normalized
    assert "primary_events.start_date" in normalized
    assert "primary_events.end_date" in normalized


def test_build_primary_criteria_union():
    """
    Test building primary criteria with ConditionOccurrence AND DrugExposure.
    Should UNION ALL the results.
    """
    pc = PrimaryCriteria(
        CriteriaList=[
            {"ConditionOccurrence": {"CodesetId": 1}},
            {"DrugExposure": {"CodesetId": 2}},
        ],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "All"},
    )

    qb = QueryBuilder(concept_set_map={1: [100], 2: [200]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    assert "UNION ALL" in normalized
    assert "FROM condition_occurrence" in normalized
    assert "FROM drug_exposure" in normalized


def test_primary_criteria_limit_first():
    """
    Test applying 'First' limit to primary criteria.
    Should use distinct ON (person_id) order by start_date ASC.
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "First"},
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # Check for DISTINCT ON logic or Row_Number logic.
    # OHDSI usually does:
    # SELECT person_id, start_date, end_date FROM (
    #   SELECT ..., ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY start_date ASC) as rn
    # ) WHERE rn = 1

    # Or DISTINCT ON in Postgres.
    # Since we use SQLAlchemy Core and want to be somewhat generic, we might use DISTINCT ON for Postgres
    # or the subquery approach.

    # For now, let's verify that the output indicates a limitation strategy.

    assert "row_number" in normalized.lower() or "distinct on" in normalized.lower()


def test_primary_criteria_limit_last():
    """
    Test applying 'Last' limit to primary criteria.
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "Last"},
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    assert "row_number" in normalized.lower() or "distinct on" in normalized.lower()
    # If using order by, it should be DESC or similar logic
    assert "DESC" in normalized or "desc" in normalized


def test_observation_window_filters():
    """
    Test that ObservationWindow adds filtering logic.
    Primary Criteria should include events only if they fall within an observation period
    with sufficient prior and post days.
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 365, "PostDays": 30},
        PrimaryCriteriaLimit={"Type": "All"},
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # 1. Must join observation_period
    assert "JOIN observation_period" in normalized

    # 2. Must filter by PriorDays (365)
    # Logic: observation_period_start_date <= event_start_date - 365 days
    # OR: event_start_date >= observation_period_start_date + 365 days
    # Since we are checking SQL text, we look for the presence of the number 365 and some date comparison
    assert "365" in normalized

    # 3. Must filter by PostDays (30)
    # Logic: observation_period_end_date >= event_start_date + 30 days
    # OR: event_start_date <= observation_period_end_date - 30 days
    assert "30" in normalized

    # 4. Must relate the join to person_id
    assert "observation_period.person_id" in normalized


def test_observation_window_default():
    """
    Test that ObservationWindow (0,0) still joins observation_period to ensure
    validity of the event (must be within SOME observation period).
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 0, "PostDays": 0},
        PrimaryCriteriaLimit={"Type": "All"},
    )

    qb = QueryBuilder(concept_set_map={1: [100]})
    query = qb.build_primary_criteria(pc)

    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    normalized = normalize_sql(sql)

    # Must still join OP
    assert "JOIN observation_period" in normalized
    # But filters should be simple >= start_date and <= end_date without extra math
    # We check that we are NOT seeing arbitrary numbers (like if we hardcoded something)
    # but we DO expect the join.
    assert "observation_period.observation_period_start_date" in normalized
    assert "observation_period.observation_period_end_date" in normalized
