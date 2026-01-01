import pytest
from sqlalchemy import Date
from sqlalchemy.dialects import postgresql

from omop_cohort_builder.builders import QueryBuilder
from omop_cohort_builder.domain import LocationRegion, DateRange


def compile_query(query):
    return str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def test_location_region_basic():
    criteria = LocationRegion()
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = compile_query(query)

    # Should select from location_history and join location
    assert "SELECT location_history.location_history_id" in sql
    assert "JOIN location ON location_history.location_id = location.location_id" in sql

    # Verify strict domain filtering (Regression check)
    assert "location_history.domain_id = 'PERSON'" in sql


def test_location_region_start_date():
    criteria = LocationRegion(
        StartDate=DateRange(value="2020-01-01", op="gt")
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = compile_query(query)

    assert "location_history.start_date > '2020-01-01'" in sql


def test_location_region_end_date():
    criteria = LocationRegion(
        EndDate=DateRange(value="2021-01-01", op="lt")
    )
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = compile_query(query)

    assert "location_history.end_date < '2021-01-01'" in sql


def test_location_region_codeset():
    # Codeset logic is currently a pass-through/TODO, but we verify it doesn't crash
    criteria = LocationRegion(CodesetId=123)
    qb = QueryBuilder()
    query = qb.build_criteria(criteria)
    sql = compile_query(query)

    # Basic join should still be present
    assert "JOIN location ON location_history.location_id = location.location_id" in sql
