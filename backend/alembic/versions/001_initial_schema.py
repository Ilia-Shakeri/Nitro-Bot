"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('language_preference', sa.String(), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('telegram_id'),
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('receipt_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'releases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('track_url', sa.String(), nullable=False),
        sa.Column('cover_url', sa.String(), nullable=False),
        sa.Column('song_name', sa.String(), nullable=False),
        sa.Column('artist_name', sa.String(), nullable=False),
        sa.Column('legal_name', sa.String(), nullable=False),
        sa.Column('release_date', sa.String(), nullable=False),
        sa.Column('mapping_spotify', sa.String(), nullable=True),
        sa.Column('mapping_apple', sa.String(), nullable=True),
        sa.Column('requires_new_profile', sa.Boolean(), nullable=True),
        sa.Column('is_edit', sa.Boolean(), nullable=True),
        sa.Column('copyright_requested', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('releases')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
