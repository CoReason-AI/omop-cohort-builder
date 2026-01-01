from __future__ import annotations

from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    VisitOccurrence,
    ConditionEra,
    DrugEra,
    DoseEra,
    Specimen,
    DeviceExposure,
    Observation,
    Measurement,
    Death,
    ProcedureOccurrence,
    VisitDetail,
    LocationRegion,
    ObservationPeriod,
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
    concept_map = {1: [100, 101]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = ConditionOccurrence(codeset_id=1)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "condition_occurrence.condition_concept_id IN (100, 101)" in sql


def test_drug_exposure_with_codeset():
    """Test DrugExposure SQL generation with codeset_id."""
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


def test_condition_era_with_codeset():
    """Test ConditionEra SQL generation with codeset_id."""
    concept_map = {4: [400]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = ConditionEra(codeset_id=4)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "condition_era.condition_concept_id IN (400)" in sql


def test_drug_era_with_codeset():
    """Test DrugEra SQL generation with codeset_id."""
    concept_map = {5: [500]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = DrugEra(codeset_id=5)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "drug_era.drug_concept_id IN (500)" in sql


def test_dose_era_with_codeset():
    """Test DoseEra SQL generation with codeset_id."""
    concept_map = {6: [600]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = DoseEra(codeset_id=6)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "dose_era.drug_concept_id IN (600)" in sql


def test_specimen_with_codeset():
    """Test Specimen SQL generation with codeset_id."""
    concept_map = {7: [700]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = Specimen(codeset_id=7)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "specimen.specimen_concept_id IN (700)" in sql


def test_device_exposure_with_codeset():
    """Test DeviceExposure SQL generation with codeset_id."""
    concept_map = {8: [800]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = DeviceExposure(codeset_id=8)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "device_exposure.device_concept_id IN (800)" in sql


def test_observation_with_codeset():
    """Test Observation SQL generation with codeset_id."""
    concept_map = {9: [900]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = Observation(codeset_id=9)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "observation.observation_concept_id IN (900)" in sql


def test_measurement_with_codeset():
    """Test Measurement SQL generation with codeset_id."""
    concept_map = {10: [1000]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = Measurement(codeset_id=10)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "measurement.measurement_concept_id IN (1000)" in sql


def test_death_with_codeset():
    """Test Death SQL generation with codeset_id (maps to cause_concept_id)."""
    concept_map = {11: [1100]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = Death(codeset_id=11)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "death.cause_concept_id IN (1100)" in sql


def test_procedure_occurrence_with_codeset():
    """Test ProcedureOccurrence SQL generation with codeset_id."""
    concept_map = {12: [1200]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = ProcedureOccurrence(codeset_id=12)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "procedure_occurrence.procedure_concept_id IN (1200)" in sql


def test_visit_detail_with_codeset():
    """Test VisitDetail SQL generation with codeset_id."""
    concept_map = {13: [1300]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = VisitDetail(codeset_id=13)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "visit_detail.visit_detail_concept_id IN (1300)" in sql


def test_location_region_with_codeset():
    """Test LocationRegion SQL generation with codeset_id."""
    concept_map = {15: [1500]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = LocationRegion(codeset_id=15)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    # Checks join to location and filter on region_concept_id
    assert "JOIN location ON location_history.location_id = location.location_id" in sql
    assert "location.region_concept_id IN (1500)" in sql


def test_observation_period_no_codeset():
    """Test ObservationPeriod (does not use codeset_id for primary filter)."""
    # ObservationPeriod logic does not use codeset_id in the builder,
    # so we just verify it doesn't crash if someone supplied it for some reason,
    # or just that the builder works as expected without it.
    builder = QueryBuilder()
    criteria = ObservationPeriod()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "SELECT observation_period.observation_period_id" in sql


def test_codeset_not_found():
    """Test behavior when codeset_id is not found in the map."""
    builder = QueryBuilder(concept_set_map={})
    criteria = ConditionOccurrence(codeset_id=99)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    # Should resolve to empty list, resulting in IN (NULL) or similar false condition
    assert "condition_occurrence.condition_concept_id IN" in sql


def test_codeset_and_explicit_concepts():
    """Test combining codeset_id with other concept filters."""
    concept_map = {1: [100, 101]}
    builder = QueryBuilder(concept_set_map=concept_map)
    criteria = ConditionOccurrence(codeset_id=1, condition_source_concept=999)
    query = builder.build_criteria(criteria)
    sql = compile_query(query)
    assert "condition_occurrence.condition_concept_id IN (100, 101)" in sql
    assert "condition_occurrence.condition_source_concept_id = 999" in sql
