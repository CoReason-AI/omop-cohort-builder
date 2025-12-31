from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    BigInteger,
)

METADATA = MetaData()

# OMOP CDM v5.4 Condition Occurrence Table
condition_occurrence = Table(
    "condition_occurrence",
    METADATA,
    Column("condition_occurrence_id", BigInteger, primary_key=True),
    Column("person_id", BigInteger, nullable=False),
    Column("condition_concept_id", Integer, nullable=False),
    Column("condition_start_date", Date, nullable=False),
    Column("condition_start_datetime", DateTime),
    Column("condition_end_date", Date),
    Column("condition_end_datetime", DateTime),
    Column("condition_type_concept_id", Integer, nullable=False),
    Column("stop_reason", String(20)),
    Column("provider_id", BigInteger),
    Column("visit_occurrence_id", BigInteger),
    Column("visit_detail_id", BigInteger),
    Column("condition_source_value", String(50)),
    Column("condition_source_concept_id", Integer),
    Column("condition_status_source_value", String(50)),
    Column("condition_status_concept_id", Integer),
)
