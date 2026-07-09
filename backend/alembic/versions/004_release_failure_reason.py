"""add release failure reason

Revision ID: 004
Revises: 003
Create Date: 2026-07-09 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("releases", sa.Column("failure_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("releases", "failure_reason")
