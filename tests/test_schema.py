from sqlalchemy import MetaData
from omop_cohort_builder.schema import CDM_SCHEMA


def test_cdm_schema_initialization():
    """Verify that CDM_SCHEMA is a MetaData object."""
    assert isinstance(CDM_SCHEMA, MetaData)


def test_all_expected_tables_exist():
    """Verify that all required OMOP CDM tables are present in the metadata."""
    expected_tables = {
        "concept",
        "concept_ancestor",
        "person",
        "observation_period",
        "death",
        "visit_occurrence",
        "visit_detail",
        "condition_occurrence",
        "drug_exposure",
        "procedure_occurrence",
        "device_exposure",
        "measurement",
        "observation",
        "specimen",
        "location",
        "care_site",
        "provider",
        "payer_plan_period",
        "cost",
        "condition_era",
        "drug_era",
        "dose_era",
    }
    defined_tables = set(CDM_SCHEMA.tables.keys())
    missing_tables = expected_tables - defined_tables
    assert not missing_tables, f"Missing tables: {missing_tables}"


def test_person_table_columns():
    """Verify key columns in the person table."""
    person_table = CDM_SCHEMA.tables["person"]
    assert "person_id" in person_table.c
    assert "gender_concept_id" in person_table.c
    assert "year_of_birth" in person_table.c
    assert "race_concept_id" in person_table.c
    assert "ethnicity_concept_id" in person_table.c


def test_condition_occurrence_table_columns():
    """Verify key columns in the condition_occurrence table."""
    condition_table = CDM_SCHEMA.tables["condition_occurrence"]
    assert "condition_occurrence_id" in condition_table.c
    assert "person_id" in condition_table.c
    assert "condition_concept_id" in condition_table.c
    assert "condition_start_date" in condition_table.c
    assert "condition_type_concept_id" in condition_table.c


def test_drug_exposure_table_columns():
    """Verify key columns in the drug_exposure table."""
    drug_table = CDM_SCHEMA.tables["drug_exposure"]
    assert "drug_exposure_id" in drug_table.c
    assert "person_id" in drug_table.c
    assert "drug_concept_id" in drug_table.c
    assert "drug_exposure_start_date" in drug_table.c
    assert "drug_type_concept_id" in drug_table.c
    assert "days_supply" in drug_table.c
    assert "quantity" in drug_table.c


def test_visit_occurrence_table_columns():
    """Verify key columns in the visit_occurrence table."""
    visit_table = CDM_SCHEMA.tables["visit_occurrence"]
    assert "visit_occurrence_id" in visit_table.c
    assert "person_id" in visit_table.c
    assert "visit_concept_id" in visit_table.c
    assert "visit_start_date" in visit_table.c
    assert "visit_type_concept_id" in visit_table.c


def test_observation_period_table_columns():
    """Verify key columns in the observation_period table."""
    obs_period_table = CDM_SCHEMA.tables["observation_period"]
    assert "observation_period_id" in obs_period_table.c
    assert "person_id" in obs_period_table.c
    assert "observation_period_start_date" in obs_period_table.c
    assert "observation_period_end_date" in obs_period_table.c


def test_concept_table_columns():
    """Verify key columns in the concept table."""
    concept_table = CDM_SCHEMA.tables["concept"]
    assert "concept_id" in concept_table.c
    assert "concept_name" in concept_table.c
    assert "domain_id" in concept_table.c
    assert "vocabulary_id" in concept_table.c
    assert "concept_class_id" in concept_table.c
    assert "standard_concept" in concept_table.c
    assert "concept_code" in concept_table.c


def test_concept_ancestor_table_columns():
    """Verify key columns in the concept_ancestor table."""
    ca_table = CDM_SCHEMA.tables["concept_ancestor"]
    assert "ancestor_concept_id" in ca_table.c
    assert "descendant_concept_id" in ca_table.c
    assert "min_levels_of_separation" in ca_table.c
    assert "max_levels_of_separation" in ca_table.c
