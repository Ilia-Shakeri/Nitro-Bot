"""structured release metadata and charge state

Revision ID: 008
Revises: 007
Create Date: 2026-07-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("usd_amount_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "transactions",
        sa.Column("toman_amount_cents", sa.BigInteger(), nullable=True),
    )
    op.execute("UPDATE transactions SET usd_amount_cents = amount * 100")
    op.alter_column("transactions", "usd_amount_cents", server_default=None)

    op.execute(
        """
        UPDATE releases
        SET requires_new_profile = COALESCE(requires_new_profile, false),
            is_edit = COALESCE(is_edit, false),
            copyright_requested = COALESCE(copyright_requested, false)
        """
    )
    op.alter_column("releases", "requires_new_profile", nullable=False)
    op.alter_column("releases", "is_edit", nullable=False)
    op.alter_column("releases", "copyright_requested", nullable=False)
    op.add_column(
        "releases",
        sa.Column(
            "artists",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "releases",
        sa.Column(
            "legal_names",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "releases",
        sa.Column("is_rerelease", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("releases", sa.Column("original_release_date", sa.Date(), nullable=True))
    op.add_column(
        "releases",
        sa.Column("charged_cost", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("releases", sa.Column("submission_id", sa.String(length=64), nullable=True))
    op.add_column("releases", sa.Column("refunded_at", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_releases_submission_id"),
        "releases",
        ["submission_id"],
        unique=True,
    )

    op.execute(
        """
        UPDATE releases
        SET artists = jsonb_build_array(
                jsonb_build_object(
                    'name', COALESCE(NULLIF(BTRIM(artist_name), ''), 'Unknown Artist'),
                    'role', 'primary'
                )
            ),
            legal_names = jsonb_build_array(
                COALESCE(NULLIF(BTRIM(legal_name), ''), 'Unknown Legal Name')
            ),
            charged_cost = CASE
                WHEN COALESCE(is_edit, false) THEN 2
                WHEN COALESCE(requires_new_profile, false) THEN 10
                ELSE 8
            END + CASE WHEN COALESCE(copyright_requested, false) THEN 1 ELSE 0 END
        """
    )

    op.add_column("releases", sa.Column("release_date_value", sa.Date(), nullable=True))
    op.execute(
        """
        DO $$
        DECLARE
            release_row RECORD;
        BEGIN
            FOR release_row IN
                SELECT id, release_date, created_at FROM releases
            LOOP
                BEGIN
                    IF release_row.release_date !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN
                        RAISE invalid_datetime_format;
                    END IF;
                    UPDATE releases
                    SET release_date_value = release_row.release_date::date
                    WHERE id = release_row.id;
                EXCEPTION WHEN datetime_field_overflow OR invalid_datetime_format THEN
                    UPDATE releases
                    SET release_date_value = COALESCE(release_row.created_at::date, CURRENT_DATE)
                    WHERE id = release_row.id;
                END;
            END LOOP;
        END $$;
        """
    )
    op.alter_column("releases", "release_date_value", nullable=False)
    op.drop_column("releases", "release_date")
    op.alter_column("releases", "release_date_value", new_column_name="release_date")

    op.alter_column("releases", "artists", server_default=None)
    op.alter_column("releases", "legal_names", server_default=None)
    op.alter_column("releases", "is_rerelease", server_default=None)
    op.alter_column("releases", "charged_cost", server_default=None)


def downgrade() -> None:
    op.add_column("releases", sa.Column("release_date_text", sa.String(), nullable=True))
    op.execute("UPDATE releases SET release_date_text = release_date::text")
    op.alter_column("releases", "release_date_text", nullable=False)
    op.drop_column("releases", "release_date")
    op.alter_column("releases", "release_date_text", new_column_name="release_date")

    op.drop_index(op.f("ix_releases_submission_id"), table_name="releases")
    op.drop_column("releases", "refunded_at")
    op.drop_column("releases", "submission_id")
    op.drop_column("releases", "charged_cost")
    op.drop_column("releases", "original_release_date")
    op.drop_column("releases", "is_rerelease")
    op.drop_column("releases", "legal_names")
    op.drop_column("releases", "artists")
    op.alter_column("releases", "copyright_requested", nullable=True)
    op.alter_column("releases", "is_edit", nullable=True)
    op.alter_column("releases", "requires_new_profile", nullable=True)
    op.drop_column("transactions", "toman_amount_cents")
    op.drop_column("transactions", "usd_amount_cents")
