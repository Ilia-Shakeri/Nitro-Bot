from datetime import datetime
from pathlib import Path

from sqlalchemy.dialects import postgresql

from models import Release
from release_service import refund_is_due, user_for_update_statement


def test_copyright_defaults_off():
    assert Release.copyright_requested.default.arg is False


def test_credit_deduction_uses_postgres_row_lock():
    statement = user_for_update_statement(123)
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in compiled


def test_refund_guard_is_idempotent():
    assert refund_is_due(None)
    assert not refund_is_due(datetime(2026, 7, 26))


def test_migration_backfills_legacy_metadata_and_dates():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "008_structured_release_metadata.py"
    ).read_text(encoding="utf-8")
    assert "jsonb_build_object" in migration
    assert "'role', 'primary'" in migration
    assert "release_date_value" in migration
    assert "EXCEPTION WHEN datetime_field_overflow OR invalid_datetime_format" in migration
    assert "server_default=sa.false()" in migration


def test_last_name_migration_is_nullable_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "009_add_user_last_name.py"
    ).read_text(encoding="utf-8")
    assert 'sa.Column("last_name", sa.String(), nullable=True)' in migration
    assert 'op.drop_column("users", "last_name")' in migration
