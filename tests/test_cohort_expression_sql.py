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


def test_observation_window_is_noop_for_dates():
    """
    Test that observation window (PriorDays/PostDays) does NOT shift event dates in PrimaryCriteria.
    It is a filter requirement, not a date modifier.
    """
    pc = PrimaryCriteria(
        CriteriaList=[{"ConditionOccurrence": {"CodesetId": 1}}],
        ObservationWindow={"PriorDays": 5, "PostDays": 5},
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

    # Ensure NO date math is present in the select list for start/end dates
    assert " - 5" not in normalized
    assert " + 5" not in normalized
