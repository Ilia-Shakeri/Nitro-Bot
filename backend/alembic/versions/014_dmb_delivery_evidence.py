"""DMB delivery evidence and lease

Revision ID: 014
Revises: 013
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade():
    op.add_column("releases", sa.Column("source_release_id", sa.Integer(), nullable=True))
    op.add_column("releases", sa.Column("source_dmb_release_id", sa.String(128), nullable=True))
    op.add_column("releases", sa.Column("dmb_release_id", sa.String(128), nullable=True))
    op.add_column("releases", sa.Column("dmb_ean_upc", sa.String(32), nullable=True))
    op.add_column(
        "releases",
        sa.Column("dmb_isrcs", _json_type(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "releases",
        sa.Column("dmb_submission_started_at", sa.DateTime(), nullable=True),
    )
    op.add_column("releases", sa.Column("dmb_submitted_at", sa.DateTime(), nullable=True))
    op.add_column("releases", sa.Column("dmb_evidence_path", sa.String(512), nullable=True))
    op.add_column("releases", sa.Column("dmb_last_error", sa.Text(), nullable=True))
    op.add_column(
        "releases",
        sa.Column("dmb_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("releases", sa.Column("dmb_lease_owner", sa.String(128), nullable=True))
    op.add_column("releases", sa.Column("dmb_lease_expires_at", sa.DateTime(), nullable=True))
    op.add_column("releases", sa.Column("dmb_reviewed_by", sa.String(128), nullable=True))
    op.add_column("releases", sa.Column("dmb_reviewed_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_releases_source_release_id",
        "releases",
        "releases",
        ["source_release_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_releases_dmb_attempts_nonnegative",
        "releases",
        "dmb_attempts >= 0",
    )
    op.drop_constraint("ck_releases_status_allowed", "releases", type_="check")
    op.create_check_constraint(
        "ck_releases_status_allowed",
        "releases",
        "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'dmb_verification_required', 'completed', 'failed')",
    )
    op.create_index(
        "ix_releases_dmb_claim",
        "releases",
        ["status", "is_edit", "dmb_lease_expires_at"],
    )


def downgrade():
    op.drop_index("ix_releases_dmb_claim", table_name="releases")
    op.drop_constraint("ck_releases_dmb_attempts_nonnegative", "releases", type_="check")
    op.drop_constraint("ck_releases_status_allowed", "releases", type_="check")
    op.create_check_constraint(
        "ck_releases_status_allowed",
        "releases",
        "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'completed', 'failed')",
    )
    op.drop_constraint("fk_releases_source_release_id", "releases", type_="foreignkey")
    for column in (
        "dmb_reviewed_at",
        "dmb_reviewed_by",
        "dmb_lease_expires_at",
        "dmb_lease_owner",
        "dmb_attempts",
        "dmb_last_error",
        "dmb_evidence_path",
        "dmb_submitted_at",
        "dmb_submission_started_at",
        "dmb_isrcs",
        "dmb_ean_upc",
        "dmb_release_id",
        "source_dmb_release_id",
        "source_release_id",
    ):
        op.drop_column("releases", column)
