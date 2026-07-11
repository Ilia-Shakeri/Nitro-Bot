"""add profile email to releases

Revision ID: 005
Revises: 004
Create Date: 2026-07-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("releases", sa.Column("profile_email", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("releases", "profile_email")
