from datetime import datetime
from pathlib import Path

from sqlalchemy.dialects import postgresql

from models import Release, Transaction
from release_service import refund_is_due, user_for_update_statement
from routers.internal import claimable_release_statement


def test_copyright_defaults_off():
    assert Release.copyright_requested.default.arg is False


def test_explicit_content_defaults_off():
    assert Release.explicit_content.default.arg is False


def test_credit_deduction_uses_postgres_row_lock():
    statement = user_for_update_statement(123)
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in compiled


def test_dmb_release_claim_uses_skip_locked_row_lock():
    compiled = str(claimable_release_statement().compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE SKIP LOCKED" in compiled
    assert "LIMIT" in compiled


def test_refund_guard_is_idempotent():
    assert refund_is_due(None)
    assert not refund_is_due(datetime(2026, 7, 26))


def test_transaction_has_quote_and_stars_reconciliation_fields():
    for field in (
        "quote_asset",
        "quote_network",
        "quoted_amount",
        "quoted_usd_rate",
        "quote_created_at",
        "quote_expires_at",
        "stars_amount",
        "invoice_payload",
        "provider_charge_id",
    ):
        assert hasattr(Transaction, field)


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


def test_artist_mapping_policy_and_payment_migration_is_backward_compatible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "010_artist_mappings_policy_and_payment_quotes.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "009"' in migration
    assert '"artist_mappings"' in migration
    assert "mapping_spotify" in migration
    assert "requires_new_profile" in migration
    assert '"policy_accepted_at"' in migration
    assert '"invoice_payload"' in migration
    assert "def downgrade()" in migration
    assert 'op.drop_column("releases", "artist_mappings")' in migration


def test_explicit_content_migration_is_safe_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "011_add_release_explicit_content.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "010"' in migration
    assert '"explicit_content"' in migration
    assert "server_default=sa.false()" in migration
    assert 'op.drop_column("releases", "explicit_content")' in migration
