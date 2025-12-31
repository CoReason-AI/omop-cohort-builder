from __future__ import annotations

import pytest
from sqlalchemy.dialects import postgresql
from pydantic import ValidationError

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import (
    ConditionOccurrence,
    DrugExposure,
    ProcedureOccurrence,
    Death,
)
from omop_cohort_builder.base import TextFilter, NumericRange, Concept, DateRange


def compile_query(query):
    """Helper to compile query to string for assertions."""
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


# --- ConditionOccurrence Tests ---


def test_condition_occurrence_basic():
    """Test ConditionOccurrence query generation without filters."""
    criteria = ConditionOccurrence()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT condition_occurrence.condition_occurrence_id" in sql
    assert "FROM condition_occurrence" in sql


def test_condition_occurrence_condition_type():
    """Test ConditionOccurrence query generation with condition_type filter."""
    concept = Concept(
        CONCEPT_ID=123,
        CONCEPT_NAME="Test Concept",
        DOMAIN_ID="Condition",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Clinical Finding",
    )
    criteria = ConditionOccurrence(condition_type=[concept])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE condition_occurrence.condition_type_concept_id IN (123)" in sql


def test_condition_occurrence_condition_type_empty_list():
    """Test ConditionOccurrence query generation with empty condition_type list."""
    criteria = ConditionOccurrence(condition_type=[])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    # Should not have WHERE clause for condition_type
    assert "condition_occurrence.condition_type_concept_id IN" not in sql


def test_condition_occurrence_source_concept():
    """Test ConditionOccurrence query generation with source concept filter."""
    criteria = ConditionOccurrence(condition_source_concept=456)
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "WHERE condition_occurrence.condition_source_concept_id = 456" in sql


def test_condition_occurrence_multiple_filters():
    """Test ConditionOccurrence with multiple filters."""
    concept = Concept(
        CONCEPT_ID=123,
        CONCEPT_NAME="Test Concept",
        DOMAIN_ID="Condition",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Clinical Finding",
    )
    criteria = ConditionOccurrence(
        condition_type=[concept], condition_source_concept=456
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "condition_occurrence.condition_type_concept_id IN (123)" in sql
    assert "condition_occurrence.condition_source_concept_id = 456" in sql
    assert "AND" in sql


def test_unimplemented_criteria_raises_error():
    """Test that unimplemented criteria types raise NotImplementedError."""
    # Using Death as a dummy unimplemented criteria
    criteria = Death()
    builder = QueryBuilder()

    with pytest.raises(NotImplementedError) as exc:
        builder.build_criteria(criteria)

    assert "Query builder not implemented for type" in str(exc.value)


# --- DrugExposure Tests ---


def test_drug_exposure_basic():
    """Test DrugExposure query generation without filters."""
    criteria = DrugExposure()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)

    sql = compile_query(query)
    assert "SELECT drug_exposure.drug_exposure_id" in sql
    assert "FROM drug_exposure" in sql


def test_drug_exposure_scalar_filters():
    """Test DrugExposure with scalar filters (TextFilter, NumericRange, int)."""
    criteria = DrugExposure(
        stop_reason=TextFilter(text="stopped", op="eq"),
        refills=NumericRange(value=1, op="gt"),
        quantity=NumericRange(value=10, op="lte"),
        days_supply=NumericRange(value=30, op="eq"),
        lot_number=TextFilter(text="LOT123", op="eq"),
        drug_source_concept=999,
    )
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "drug_exposure.stop_reason = 'stopped'" in sql
    assert "drug_exposure.refills > 1" in sql
    assert "drug_exposure.quantity <= 10" in sql
    assert "drug_exposure.days_supply = 30" in sql
    assert "drug_exposure.lot_number = 'LOT123'" in sql
    assert "drug_exposure.drug_source_concept_id = 999" in sql


def test_drug_exposure_concept_filters():
    """Test DrugExposure with concept list filters."""
    c1 = Concept(
        CONCEPT_ID=101,
        CONCEPT_NAME="Drug A",
        DOMAIN_ID="Drug",
        VOCABULARY_ID="RxNorm",
        CONCEPT_CLASS_ID="Drug",
    )
    c2 = Concept(
        CONCEPT_ID=102,
        CONCEPT_NAME="Route Oral",
        DOMAIN_ID="Route",
        VOCABULARY_ID="SNOMED",
        CONCEPT_CLASS_ID="Route",
    )

    criteria = DrugExposure(drug_type=[c1], route_concept=[c2])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "drug_exposure.drug_type_concept_id IN (101)" in sql
    assert "drug_exposure.route_concept_id IN (102)" in sql


def test_numeric_filter_ops():
    """Test all numeric filter operations to ensure coverage."""
    # gt tested above
    # lt
    criteria_lt = DrugExposure(refills=NumericRange(value=5, op="lt"))
    sql_lt = compile_query(QueryBuilder().build_criteria(criteria_lt))
    assert "drug_exposure.refills < 5" in sql_lt

    # eq tested above
    # gte
    criteria_gte = DrugExposure(refills=NumericRange(value=5, op="gte"))
    sql_gte = compile_query(QueryBuilder().build_criteria(criteria_gte))
    assert "drug_exposure.refills >= 5" in sql_gte

    # lte tested above

    # bt
    criteria_bt = DrugExposure(refills=NumericRange(value=5, op="bt", extent=10))
    sql_bt = compile_query(QueryBuilder().build_criteria(criteria_bt))
    assert "drug_exposure.refills BETWEEN 5 AND 10" in sql_bt

    # !bt
    criteria_nbt = DrugExposure(refills=NumericRange(value=5, op="!bt", extent=10))
    sql_nbt = compile_query(QueryBuilder().build_criteria(criteria_nbt))
    assert "drug_exposure.refills NOT BETWEEN 5 AND 10" in sql_nbt

    # bt with no extent (should be ignored or handled? Code currently requires extent != None for bt logic)
    criteria_bt_no_ext = DrugExposure(refills=NumericRange(value=5, op="bt"))
    sql_bt_no_ext = compile_query(QueryBuilder().build_criteria(criteria_bt_no_ext))
    # It should effectively return the base query without that filter if extent is None in the code block
    assert "drug_exposure.refills BETWEEN" not in sql_bt_no_ext

    # !bt with no extent
    criteria_nbt_no_ext = DrugExposure(refills=NumericRange(value=5, op="!bt"))
    sql_nbt_no_ext = compile_query(QueryBuilder().build_criteria(criteria_nbt_no_ext))
    assert "drug_exposure.refills NOT BETWEEN" not in sql_nbt_no_ext


def test_numeric_filter_unknown_op():
    """Test numeric filter with an unknown operator (fall through)."""
    # Note: Pydantic validation prevents strict unknown ops now.
    # We must bypass validation or assume this test is now obsolete regarding "unknown" string.
    # If we really want to test the builder's behavior on 'weird' input, we can mock it, but
    # strictly speaking Pydantic guarantees valid Enums.

    # Let's try to construct a 'fake' object that bypasses validation if we really need to test the builder fall-through
    # But for now, we expect ValidationError if we try to pass "unknown"
    with pytest.raises(ValidationError):
        DrugExposure(refills=NumericRange(value=5, op="unknown"))


def test_text_filter_coverage():
    """Test text filter coverage with various ops."""

    # 1. contains -> LIKE %...%
    criteria_contains = DrugExposure(
        stop_reason=TextFilter(text="reason", op="contains")
    )
    sql_contains = compile_query(QueryBuilder().build_criteria(criteria_contains))
    assert "drug_exposure.stop_reason LIKE '%%reason%%'" in sql_contains

    # 2. startsWith -> LIKE ...%
    criteria_starts = DrugExposure(
        stop_reason=TextFilter(text="start", op="startsWith")
    )
    sql_starts = compile_query(QueryBuilder().build_criteria(criteria_starts))
    assert "drug_exposure.stop_reason LIKE 'start%%'" in sql_starts

    # 3. endsWith -> LIKE %...
    criteria_ends = DrugExposure(stop_reason=TextFilter(text="end", op="endsWith"))
    sql_ends = compile_query(QueryBuilder().build_criteria(criteria_ends))
    assert "drug_exposure.stop_reason LIKE '%%end'" in sql_ends

    # 4. !eq -> !=
    criteria_neq = DrugExposure(stop_reason=TextFilter(text="notme", op="!eq"))
    sql_neq = compile_query(QueryBuilder().build_criteria(criteria_neq))
    assert "drug_exposure.stop_reason != 'notme'" in sql_neq

    # 5. !contains -> NOT LIKE %...%
    criteria_ncontains = DrugExposure(stop_reason=TextFilter(text="no", op="!contains"))
    sql_ncontains = compile_query(QueryBuilder().build_criteria(criteria_ncontains))
    assert "drug_exposure.stop_reason NOT LIKE '%%no%%'" in sql_ncontains

    # 6. !startsWith -> NOT LIKE ...%
    criteria_nstarts = DrugExposure(
        stop_reason=TextFilter(text="nostart", op="!startsWith")
    )
    sql_nstarts = compile_query(QueryBuilder().build_criteria(criteria_nstarts))
    assert "drug_exposure.stop_reason NOT LIKE 'nostart%%'" in sql_nstarts

    # 7. !endsWith -> NOT LIKE %...
    criteria_nends = DrugExposure(stop_reason=TextFilter(text="noend", op="!endsWith"))
    sql_nends = compile_query(QueryBuilder().build_criteria(criteria_nends))
    assert "drug_exposure.stop_reason NOT LIKE '%%noend'" in sql_nends

    # 8. fallback (unknown op or 'like') -> LIKE ...
    criteria_like = DrugExposure(stop_reason=TextFilter(text="raw%", op="like"))
    sql_like = compile_query(QueryBuilder().build_criteria(criteria_like))
    # Standard LIKE should take the text as is.
    assert "drug_exposure.stop_reason LIKE 'raw%%'" in sql_like


def test_dose_unit_ignored():
    """Test that dose_unit filter is currently ignored (TODO implementation)."""
    c1 = Concept(
        CONCEPT_ID=103,
        CONCEPT_NAME="mg",
        DOMAIN_ID="Unit",
        VOCABULARY_ID="UCUM",
        CONCEPT_CLASS_ID="Unit",
    )
    criteria = DrugExposure(dose_unit=[c1])
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    # Should select from drug_exposure but NOT filter by dose_unit (as it's a TODO)
    assert "SELECT drug_exposure.drug_exposure_id" in sql
    # We verify it DOES NOT try to filter on a non-existent column or the old one we removed
    assert "dose_unit_concept_id" not in sql


# --- ProcedureOccurrence Tests ---


def test_procedure_occurrence_basic():
    """Test ProcedureOccurrence query generation without filters."""
    criteria = ProcedureOccurrence()
    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "SELECT procedure_occurrence.procedure_occurrence_id" in sql
    assert "FROM procedure_occurrence" in sql


def test_procedure_occurrence_all_filters():
    """Test ProcedureOccurrence with all supported filters."""
    c1 = Concept(
        CONCEPT_ID=301,
        CONCEPT_NAME="Surgery",
        DOMAIN_ID="Procedure",
        VOCABULARY_ID="CPT4",
    )
    c2 = Concept(
        CONCEPT_ID=302,
        CONCEPT_NAME="Modifier",
        DOMAIN_ID="Modifier",
        VOCABULARY_ID="CPT4",
    )

    criteria = ProcedureOccurrence(
        procedure_type=[c1],
        modifier=[c2],
        quantity=NumericRange(value=2, op="gte"),
        procedure_source_concept=303,
        occurrence_start_date=DateRange(value="2021-01-01", op="eq"),
    )

    builder = QueryBuilder()
    query = builder.build_criteria(criteria)
    sql = compile_query(query)

    assert "procedure_occurrence.procedure_type_concept_id IN (301)" in sql
    assert "procedure_occurrence.modifier_concept_id IN (302)" in sql
    assert "procedure_occurrence.quantity >= 2" in sql
    assert "procedure_occurrence.procedure_source_concept_id = 303" in sql
    assert "procedure_occurrence.procedure_date = '2021-01-01'" in sql


def test_date_filter_ops():
    """Test all date filter operations to ensure coverage."""
    # We can use ProcedureOccurrence for this
    # eq tested in procedure basic

    # gt
    criteria_gt = ProcedureOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="gt")
    )
    sql_gt = compile_query(QueryBuilder().build_criteria(criteria_gt))
    assert "procedure_occurrence.procedure_date > '2020-01-01'" in sql_gt

    # lt
    criteria_lt = ProcedureOccurrence(
        occurrence_start_date=DateRange(value="2020-01-01", op="lt")
    )
    sql_lt = compile_query(QueryBuilder().build_criteria(criteria_lt))
    assert "procedure_occurrence.procedure_date < '2020-01-01'" in sql_lt

    # bt
    criteria_bt = ProcedureOccurrence(
        occurrence_start_date=DateRange(
            value="2020-01-01", op="bt", extent="2020-12-31"
        )
    )
    sql_bt = compile_query(QueryBuilder().build_criteria(criteria_bt))
    assert (
        "procedure_occurrence.procedure_date BETWEEN '2020-01-01' AND '2020-12-31'"
        in sql_bt
    )

    # !bt
    criteria_nbt = ProcedureOccurrence(
        occurrence_start_date=DateRange(
            value="2020-01-01", op="!bt", extent="2020-12-31"
        )
    )
    sql_nbt = compile_query(QueryBuilder().build_criteria(criteria_nbt))
    assert (
        "procedure_occurrence.procedure_date NOT BETWEEN '2020-01-01' AND '2020-12-31'"
        in sql_nbt
    )
