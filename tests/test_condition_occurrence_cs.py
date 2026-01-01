from __future__ import annotations

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import ConditionOccurrence
from omop_cohort_builder.base import ConceptSetSelection
from sqlalchemy.dialects import postgresql
from sqlalchemy import select, table, column


def compile_query(query):
    return query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )


def normalize(s):
    return " ".join(s.split())


def test_build_condition_occurrence_condition_type_cs_inclusion():
    """Test condition_type_cs inclusion logic."""
    # codeset_id 1 -> [10, 20]
    qb = QueryBuilder(concept_set_map={1: [10, 20]})
    criteria = ConditionOccurrence(
        condition_type_cs=ConceptSetSelection(codeset_id=1, is_exclusion=False)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    assert "condition_occurrence.condition_type_concept_id IN (10, 20)" in sql


def test_build_condition_occurrence_condition_type_cs_exclusion():
    """Test condition_type_cs exclusion logic."""
    # codeset_id 1 -> [10, 20]
    qb = QueryBuilder(concept_set_map={1: [10, 20]})
    criteria = ConditionOccurrence(
        condition_type_cs=ConceptSetSelection(codeset_id=1, is_exclusion=True)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    assert "condition_occurrence.condition_type_concept_id NOT IN (10, 20)" in sql


def test_build_condition_occurrence_condition_status_cs_inclusion():
    """Test condition_status_cs inclusion logic."""
    # codeset_id 2 -> [30, 40]
    qb = QueryBuilder(concept_set_map={2: [30, 40]})
    criteria = ConditionOccurrence(
        condition_status_cs=ConceptSetSelection(codeset_id=2, is_exclusion=False)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    assert "condition_occurrence.condition_status_concept_id IN (30, 40)" in sql


def test_build_condition_occurrence_condition_status_cs_exclusion():
    """Test condition_status_cs exclusion logic."""
    # codeset_id 2 -> [30, 40]
    qb = QueryBuilder(concept_set_map={2: [30, 40]})
    criteria = ConditionOccurrence(
        condition_status_cs=ConceptSetSelection(codeset_id=2, is_exclusion=True)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    assert "condition_occurrence.condition_status_concept_id NOT IN (30, 40)" in sql


def test_build_condition_occurrence_cs_empty_inclusion():
    """Test empty codeset with inclusion (should result in False condition)."""
    # codeset_id 3 -> []
    qb = QueryBuilder(concept_set_map={3: []})
    criteria = ConditionOccurrence(
        condition_type_cs=ConceptSetSelection(codeset_id=3, is_exclusion=False)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    # SQLAlchemy typically renders literal(False) as 'false' or '0 = 1' depending on dialect.
    # Postgres dialect: 'false'
    assert "false" in sql or "0 = 1" in sql or "1 != 1" in sql


def test_build_condition_occurrence_cs_empty_exclusion():
    """Test empty codeset with exclusion (should result in no-op/True)."""
    # codeset_id 3 -> []
    qb = QueryBuilder(concept_set_map={3: []})
    criteria = ConditionOccurrence(
        condition_type_cs=ConceptSetSelection(codeset_id=3, is_exclusion=True)
    )

    query = qb.build_criteria(criteria)
    sql = normalize(str(compile_query(query)))

    # Should have no WHERE clause related to this filter
    # Note: The column is present in the SELECT clause, so we check for its absence in a WHERE context
    # or simpler, just check that there is no WHERE clause if this is the only filter.
    assert "WHERE" not in sql


def test_apply_concept_set_selection_edge_cases():
    """Test edge cases for _apply_concept_set_selection directly."""
    qb = QueryBuilder()
    t = table("t", column("c"))
    query = select(t)

    # Test selection is None
    result = qb._apply_concept_set_selection(query, t.c.c, None)
    assert result is query

    # Test selection.codeset_id is None (simulated via bypass)
    class MockSelection:
        codeset_id = None
        is_exclusion = False

    result = qb._apply_concept_set_selection(query, t.c.c, MockSelection())
    assert result is query
