import pytest
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import Specimen
from omop_cohort_builder.base import (
    Concept,
    NumericRange,
    DateRange,
    TextFilter,
)


@pytest.fixture
def builder():
    return QueryBuilder()


def test_specimen_sql_generation(builder):
    """
    Tests SQL generation for Specimen criteria.
    """
    criteria = Specimen(
        specimen_type=[
            Concept(
                CONCEPT_ID=1001,
                CONCEPT_NAME="Blood",
                DOMAIN_ID="Specimen",
                VOCABULARY_ID="SNOMED",
                CONCEPT_CLASS_ID="Specimen",
            )
        ],
        quantity=NumericRange(value=10, op="gt"),
        unit=[
            Concept(
                CONCEPT_ID=2001,
                CONCEPT_NAME="mL",
                DOMAIN_ID="Unit",
                VOCABULARY_ID="UCUM",
                CONCEPT_CLASS_ID="Unit",
            )
        ],
        anatomic_site=[
            Concept(
                CONCEPT_ID=3001,
                CONCEPT_NAME="Arm",
                DOMAIN_ID="Specimen",
                VOCABULARY_ID="SNOMED",
                CONCEPT_CLASS_ID="Specimen",
            )
        ],
        disease_status=[
            Concept(
                CONCEPT_ID=4001,
                CONCEPT_NAME="Normal",
                DOMAIN_ID="Specimen",
                VOCABULARY_ID="SNOMED",
                CONCEPT_CLASS_ID="Specimen",
            )
        ],
        source_id=TextFilter(text="SID123", op="eq"),
        occurrence_start_date=DateRange(value="2023-01-01", op="gt"),
    )

    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    # Normalize whitespace
    sql = " ".join(sql.split())

    assert "SELECT specimen.specimen_id, specimen.person_id" in sql
    assert "FROM specimen" in sql
    assert "specimen.specimen_type_concept_id IN (1001)" in sql
    assert "specimen.quantity > 10" in sql
    assert "specimen.unit_concept_id IN (2001)" in sql
    assert "specimen.anatomic_site_concept_id IN (3001)" in sql
    assert "specimen.disease_status_concept_id IN (4001)" in sql
    assert "specimen.specimen_source_id = 'SID123'" in sql
    assert "specimen.specimen_date > '2023-01-01'" in sql


def test_specimen_sql_minimal(builder):
    """
    Tests SQL generation for minimal Specimen criteria (no filters).
    """
    criteria = Specimen()
    query = builder.build_criteria(criteria)
    sql = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    # Normalize whitespace
    sql = " ".join(sql.split())

    assert "SELECT specimen.specimen_id" in sql
    assert "FROM specimen" in sql
    # Ensure no WHERE clause is generated if no filters are present (except implied ones if any)
    # The default select might not have a WHERE clause.
    # We check that specific filters are NOT present in the WHERE clause (so check for "WHERE ...")
    assert "WHERE" not in sql
