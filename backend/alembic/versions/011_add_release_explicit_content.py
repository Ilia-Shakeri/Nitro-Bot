"""add explicit content flag to releases

Revision ID: 011
Revises: 010
"""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "releases",
        sa.Column(
            "explicit_content",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("releases", "explicit_content")
