"""release input and state constraints

Revision ID: 013
Revises: 012
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "credits", existing_type=sa.Integer(), nullable=False)
    op.alter_column("releases", "status", existing_type=sa.String(), nullable=False)
    op.create_check_constraint(
        "ck_users_credits_nonnegative",
        "users",
        "credits >= 0",
    )
    op.create_check_constraint(
        "ck_releases_charged_cost_nonnegative",
        "releases",
        "charged_cost >= 0",
    )
    op.create_check_constraint(
        "ck_releases_status_allowed",
        "releases",
        "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'completed', 'failed')",
    )
    op.create_check_constraint(
        "ck_release_jobs_attempts_nonnegative",
        "release_jobs",
        "attempts >= 0",
    )
    op.create_check_constraint(
        "ck_release_jobs_phase_allowed",
        "release_jobs",
        "phase IN ('media', 'notify')",
    )
    op.create_check_constraint(
        "ck_release_jobs_status_allowed",
        "release_jobs",
        "status IN ('queued', 'processing', 'retry', 'completed', 'dead')",
    )


def downgrade():
    op.drop_constraint("ck_release_jobs_status_allowed", "release_jobs", type_="check")
    op.drop_constraint("ck_release_jobs_phase_allowed", "release_jobs", type_="check")
    op.drop_constraint("ck_release_jobs_attempts_nonnegative", "release_jobs", type_="check")
    op.drop_constraint("ck_releases_status_allowed", "releases", type_="check")
    op.drop_constraint("ck_releases_charged_cost_nonnegative", "releases", type_="check")
    op.drop_constraint("ck_users_credits_nonnegative", "users", type_="check")
    op.alter_column("releases", "status", existing_type=sa.String(), nullable=True)
    op.alter_column("users", "credits", existing_type=sa.Integer(), nullable=True)
