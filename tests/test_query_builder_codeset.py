from __future__ import annotations

from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
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
)


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_query_builder_init_with_map():
    """Test initializing QueryBuilder with a concept set map."""
    concept_map = {1: [100, 101], 2: [200]}
    builder = QueryBuilder(concept_set_map=concept_map)
    assert builder.concept_set_map == concept_map
    assert builder._resolve_codeset(1) == [100, 101]
    assert builder._resolve_codeset(2) == [200]
    assert builder._resolve_codeset(99) == []


def test_condition_occurrence_with_codeset():
    """Test ConditionOccurrence SQL generation with codeset_id."""
    # Setup: Codeset 1 maps to concept IDs 100 and 101
    concept_map = {1: [100, 101]}
    builder = QueryBuilder(concept_set_map=concept_map)

    # Criteria uses CodesetId 1
    criteria = ConditionOccurrence(codeset_id=1)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Verify SQL contains IN clause with resolved concepts
    assert "condition_occurrence.condition_concept_id IN (100, 101)" in sql


def test_drug_exposure_with_codeset():
    """Test DrugExposure SQL generation with codeset_id."""
    # Setup: Codeset 2 maps to concept IDs 200, 201, 202
    concept_map = {2: [200, 201, 202]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = DrugExposure(codeset_id=2)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "drug_exposure.drug_concept_id IN (200, 201, 202)" in sql


def test_visit_occurrence_with_codeset():
    """Test VisitOccurrence SQL generation with codeset_id."""
    concept_map = {3: [300]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = VisitOccurrence(codeset_id=3)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "visit_occurrence.visit_concept_id IN (300)" in sql


def test_procedure_occurrence_with_codeset():
    """Test ProcedureOccurrence SQL generation with codeset_id."""
    concept_map = {4: [400, 401]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = ProcedureOccurrence(codeset_id=4)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "procedure_occurrence.procedure_concept_id IN (400, 401)" in sql


def test_measurement_with_codeset():
    """Test Measurement SQL generation with codeset_id."""
    concept_map = {5: [500]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = Measurement(codeset_id=5)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "measurement.measurement_concept_id IN (500)" in sql


def test_observation_with_codeset():
    """Test Observation SQL generation with codeset_id."""
    concept_map = {6: [600]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = Observation(codeset_id=6)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "observation.observation_concept_id IN (600)" in sql


def test_device_exposure_with_codeset():
    """Test DeviceExposure SQL generation with codeset_id."""
    concept_map = {7: [700]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = DeviceExposure(codeset_id=7)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "device_exposure.device_concept_id IN (700)" in sql


def test_death_with_codeset():
    """Test Death SQL generation with codeset_id."""
    concept_map = {8: [800]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = Death(codeset_id=8)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "death.cause_concept_id IN (800)" in sql


def test_specimen_with_codeset():
    """Test Specimen SQL generation with codeset_id."""
    concept_map = {9: [900]}
    builder = QueryBuilder(concept_set_map=concept_map)

    criteria = Specimen(codeset_id=9)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "specimen.specimen_concept_id IN (900)" in sql


def test_codeset_not_found():
    """Test behavior when codeset_id is not found in the map."""
    builder = QueryBuilder(concept_set_map={})

    # Criteria refers to non-existent codeset 99
    criteria = ConditionOccurrence(codeset_id=99)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Should resolve to empty list.
    assert "condition_occurrence.condition_concept_id IN" in sql


def test_codeset_and_explicit_concepts():
    """Test combining codeset_id with other concept filters (AND logic)."""
    concept_map = {1: [100, 101]}
    builder = QueryBuilder(concept_set_map=concept_map)

    # Criteria has both codeset_id AND condition_source_concept
    criteria = ConditionOccurrence(codeset_id=1, condition_source_concept=999)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "condition_occurrence.condition_concept_id IN (100, 101)" in sql
    assert "condition_occurrence.condition_source_concept_id = 999" in sql
    assert "AND" in sql
