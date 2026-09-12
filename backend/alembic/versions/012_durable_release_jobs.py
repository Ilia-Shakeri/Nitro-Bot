"""durable release jobs and failure reason

Revision ID: 012
Revises: 011
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("releases", sa.Column("failure_reason", sa.String(length=255), nullable=True))
    op.create_table(
        "release_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("release_id", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False, server_default="media"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("source_audio_key", sa.String(), nullable=False),
        sa.Column("source_cover_key", sa.String(), nullable=False),
        sa.Column("convert_audio", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("convert_cover", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_release_jobs_release_id", "release_jobs", ["release_id"], unique=True)


def downgrade():
    op.drop_index("ix_release_jobs_release_id", table_name="release_jobs")
    op.drop_table("release_jobs")
    op.drop_column("releases", "failure_reason")
