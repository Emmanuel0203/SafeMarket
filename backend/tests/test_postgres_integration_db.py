"""
PostgreSQL integration tests for SafeMarket backend.

These tests validate:
1) Connectivity using SQLAlchemy engine configured in the app.
2) Presence of core tables expected by the enhanced schema.
3) Basic insert/query/delete flow on companies and users tables.
"""

from __future__ import annotations

import uuid

from sqlalchemy import inspect, text

from db import engine


EXPECTED_CORE_TABLES = {
    "companies",
    "users",
    "devices",
    "sessions",
    "transactions",
    "risk_scores",
    "alerts",
}


def test_db_connection_works() -> None:
    """Database accepts connections and basic SQL."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()
    assert result == 1


def test_core_tables_exist() -> None:
    """Enhanced schema tables were created in PostgreSQL."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing_tables = EXPECTED_CORE_TABLES - existing_tables
    assert not missing_tables, f"Missing tables: {sorted(missing_tables)}"


def test_company_user_roundtrip() -> None:
    """Create and read data with SQL (transaction rolled back)."""
    company_name = f"test_company_{uuid.uuid4().hex[:8]}"
    email = f"test_{uuid.uuid4().hex[:8]}@safemarket.local"
    with engine.connect() as connection:
        tx = connection.begin()
        try:
            company_id = connection.execute(
                text(
                    """
                    INSERT INTO companies (name, industry, country_code)
                    VALUES (:name, :industry, :country_code)
                    RETURNING company_id
                    """
                ),
                {"name": company_name, "industry": "QA", "country_code": "PE"},
            ).scalar_one()

            user_id = connection.execute(
                text(
                    """
                    INSERT INTO users (email, hashed_password, company_id, role, status)
                    VALUES (:email, :hashed_password, :company_id, :role, :status)
                    RETURNING user_id
                    """
                ),
                {
                    "email": email,
                    "hashed_password": "fake-hash-for-integration-test",
                    "company_id": company_id,
                    "role": "VIEWER",
                    "status": "ACTIVE",
                },
            ).scalar_one()

            loaded_email = connection.execute(
                text("SELECT email FROM users WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).scalar_one()
            assert loaded_email == email
        finally:
            tx.rollback()
