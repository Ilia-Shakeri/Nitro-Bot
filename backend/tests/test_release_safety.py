from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from models import Release, ReleaseJob, Transaction
from release_jobs import claimable_job_statement, retry_delay_seconds
from release_service import refund_is_due, user_for_update_statement
from routers import internal
from routers import releases
from routers.releases import build_edit_diff
from routers.internal import (
    _STATUS_TRANSITIONS,
    _parse_evidence,
    _parse_submit_checkpoint,
    _submission_fingerprint,
    claimable_release_statement,
    resolve_release_verification,
)


def test_copyright_defaults_off():
    assert Release.copyright_requested.default.arg is False


def test_explicit_content_defaults_off():
    assert Release.explicit_content.default.arg is False


def test_edit_diff_keeps_only_changed_values():
    diff = build_edit_diff(
        {"song_name": "Old", "genre": "Pop", "release_date": datetime(2026, 1, 1)},
        {"song_name": "New", "genre": "Pop", "release_date": datetime(2026, 1, 2)},
    )
    assert diff == {
        "song_name": {"from": "Old", "to": "New"},
        "release_date": {
            "from": "2026-01-01T00:00:00",
            "to": "2026-01-02T00:00:00",
        },
    }


def test_credit_deduction_uses_postgres_row_lock():
    statement = user_for_update_statement(123)
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in compiled


def test_dmb_release_claim_uses_skip_locked_row_lock():
    compiled = str(
        claimable_release_statement("create", datetime(2026, 9, 13)).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "FOR UPDATE SKIP LOCKED" in compiled
    assert "LIMIT" in compiled
    assert "dmb_lease_expires_at" in compiled
    assert "dmb_lease_expires_at IS NULL" in compiled
    assert "dmb_attempts" in compiled


def test_release_job_claim_recovers_expired_leases_with_row_lock():
    statement = claimable_job_statement(datetime(2026, 9, 12))
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "release_jobs.lease_expires_at" in compiled
    assert "FOR UPDATE SKIP LOCKED" in compiled
    assert "LIMIT" in compiled


def test_release_job_has_durable_retry_fields():
    for field in (
        "phase",
        "status",
        "attempts",
        "lease_owner",
        "lease_expires_at",
        "next_attempt_at",
        "last_error",
    ):
        assert hasattr(ReleaseJob, field)
    assert retry_delay_seconds(1) == 1
    assert retry_delay_seconds(20) == 300


def test_refund_guard_is_idempotent():
    assert refund_is_due(None)
    assert not refund_is_due(datetime(2026, 7, 26))


def test_terminal_release_cannot_be_changed_to_failed():
    assert "failed" not in _STATUS_TRANSITIONS["completed"]
    assert "failed" not in _STATUS_TRANSITIONS.get("rollback", set())


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


def test_durable_release_job_migration_is_additive_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "012_durable_release_jobs.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "011"' in migration
    assert '"release_jobs"' in migration
    assert '"lease_expires_at"' in migration
    assert '"failure_reason"' in migration
    assert 'op.drop_table("release_jobs")' in migration


def test_release_constraint_migration_is_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "013_release_input_constraints.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "012"' in migration
    assert "ck_users_credits_nonnegative" in migration
    assert "ck_releases_status_allowed" in migration
    assert "ck_release_jobs_status_allowed" in migration
    assert "op.drop_constraint" in migration


def test_container_builds_include_shared_release_data():
    root = Path(__file__).parents[2]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    backend_dockerfile = (root / "backend" / "Dockerfile").read_text(encoding="utf-8")
    frontend_dockerfile = (root / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    dmb_dockerfile = (root / "dmb-automation" / "Dockerfile").read_text(encoding="utf-8")
    assert "dockerfile: backend/Dockerfile" in compose
    assert "dockerfile: frontend/Dockerfile" in compose
    assert "COPY shared/ /shared/" in backend_dockerfile
    assert "COPY shared/ /shared/" in frontend_dockerfile
    assert "dockerfile: dmb-automation/Dockerfile" in compose
    assert "COPY shared/ /shared/" in dmb_dockerfile


def test_dmb_reviewer_secret_is_not_given_to_worker():
    compose = (Path(__file__).parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    backend_part, worker_part = compose.split("  dmb-automation:", maxsplit=1)
    assert "DMB_REVIEW_SECRET_KEY" in backend_part
    assert "DMB_REVIEW_SECRET_KEY" not in worker_part


@pytest.mark.asyncio
async def test_edit_orders_are_fail_closed_before_work(monkeypatch):
    monkeypatch.setattr(releases, "_EDIT_ENABLED", False)
    with pytest.raises(HTTPException) as exc:
        await releases.create_release(is_edit=True)
    assert exc.value.status_code == 503
    assert exc.value.detail == "dmb_edit_disabled"


@pytest.mark.asyncio
async def test_edit_audio_replacement_is_rejected_before_charge(monkeypatch):
    monkeypatch.setattr(releases, "_EDIT_ENABLED", True)
    with pytest.raises(HTTPException) as exc:
        await releases.create_release(is_edit=True, audio=MagicMock())
    assert exc.value.status_code == 400
    assert exc.value.detail == "dmb_edit_audio_not_supported"


def test_dmb_review_uses_distinct_fail_closed_secret(monkeypatch):
    monkeypatch.setattr(internal, "_SECRET", "worker-secret")
    monkeypatch.setattr(internal, "_REVIEW_SECRET", "review-secret")
    internal._require_review_secret("Bearer review-secret")
    with pytest.raises(HTTPException, match="Forbidden"):
        internal._require_review_secret("Bearer worker-secret")
    monkeypatch.setattr(internal, "_REVIEW_SECRET", "")
    with pytest.raises(HTTPException, match="review secret not configured"):
        internal._require_review_secret("Bearer review-secret")
    monkeypatch.setattr(internal, "_REVIEW_SECRET", "worker-secret")
    with pytest.raises(HTTPException, match="review secret must differ"):
        internal._require_review_secret("Bearer worker-secret")


def test_dmb_completion_evidence_is_strict_and_relative():
    assert _parse_evidence(
        "album-123",
        "1234567890123",
        '["USABC2600001"]',
        "results/42",
    ) == ("album-123", "1234567890123", ["USABC2600001"], "results/42")
    with pytest.raises(HTTPException, match="dmb_evidence_invalid"):
        _parse_evidence("album-123", "bad", "[]", "../outside")


def test_dmb_submit_checkpoint_is_bound_to_release_data():
    fingerprint = _submission_fingerprint(
        42,
        "Safe Title",
        "1234567890123",
        ["USABC2600001"],
    )
    assert _parse_submit_checkpoint(
        42,
        "Safe Title",
        "1234567890123",
        '["USABC2600001"]',
        fingerprint,
    ) == ("1234567890123", ["USABC2600001"], fingerprint)
    with pytest.raises(HTTPException, match="dmb_checkpoint_invalid"):
        _parse_submit_checkpoint(
            42,
            "Changed Title",
            "1234567890123",
            '["USABC2600001"]',
            fingerprint,
        )


def test_release_has_dmb_lease_and_evidence_fields():
    for field in (
        "source_release_id",
        "source_dmb_release_id",
        "edit_diff",
        "dmb_release_id",
        "dmb_ean_upc",
        "dmb_isrcs",
        "dmb_submission_started_at",
        "dmb_submitted_at",
        "dmb_evidence_path",
        "dmb_submission_fingerprint",
        "dmb_last_error",
        "dmb_attempts",
        "dmb_lease_owner",
        "dmb_lease_expires_at",
        "dmb_reviewed_by",
        "dmb_reviewed_at",
    ):
        assert hasattr(Release, field)


def test_edit_diff_migration_is_additive_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "017_release_edit_diff.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "016"' in migration
    assert '"edit_diff"' in migration
    assert "server_default" in migration
    assert 'op.drop_column("releases", "edit_diff")' in migration


def test_dmb_delivery_migration_is_additive_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "014_dmb_delivery_evidence.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "013"' in migration
    assert "dmb_lease_expires_at" in migration
    assert "dmb_release_id" in migration
    assert "dmb_evidence_path" in migration
    assert "dmb_reviewed_by" in migration
    assert "source_release_id" in migration
    assert "op.drop_column" in migration


def test_dmb_recovery_migration_is_additive_and_reversible():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "016_dmb_submission_recovery.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "015"' in migration
    assert "dmb_submission_fingerprint" in migration
    assert 'op.drop_column("releases", "dmb_submission_fingerprint")' in migration


@pytest.mark.asyncio
async def test_manual_verification_completion_is_audited():
    release = SimpleNamespace(
        status="dmb_verification_required",
        dmb_attempts=1,
        dmb_lease_owner=None,
        dmb_lease_expires_at=None,
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = release
    db = AsyncMock()
    db.execute.return_value = result

    response = await resolve_release_verification(
        42,
        action="completed",
        dmb_release_id="album-42",
        ean_upc="1234567890123",
        isrcs_json='["USABC2600001"]',
        evidence_path="results/42",
        reason=None,
        reviewer_id_header="ops:reviewer-1",
        db=db,
    )

    assert response == {"status": "completed"}
    assert release.status == "completed"
    assert release.dmb_release_id == "album-42"
    assert release.dmb_reviewed_by == "ops:reviewer-1"
    assert release.dmb_reviewed_at is not None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_verification_retry_keeps_attempt_limit():
    release = SimpleNamespace(
        status="dmb_verification_required",
        dmb_attempts=1,
        dmb_lease_owner=None,
        dmb_lease_expires_at=None,
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = release
    db = AsyncMock()
    db.execute.return_value = result

    response = await resolve_release_verification(
        42,
        action="retry",
        dmb_release_id=None,
        ean_upc=None,
        isrcs_json=None,
        evidence_path=None,
        reason="no remote record",
        reviewer_id_header="ops:reviewer-1",
        db=db,
    )

    assert response == {"status": "retry"}
    assert release.status == "manual_staging"
    assert release.dmb_attempts == 1
    assert release.dmb_last_error == "manual_retry:no remote record"
    db.commit.assert_awaited_once()
