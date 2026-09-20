"""DMB submission recovery fingerprint

Revision ID: 016
Revises: 015
"""

from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "releases",
        sa.Column("dmb_submission_fingerprint", sa.String(64), nullable=True),
    )


def downgrade():
    op.drop_column("releases", "dmb_submission_fingerprint")
