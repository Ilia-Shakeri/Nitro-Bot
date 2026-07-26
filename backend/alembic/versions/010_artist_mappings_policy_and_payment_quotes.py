"""artist mappings, policy audit, and payment quote fields

Revision ID: 010
Revises: 009
"""

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade():
    op.add_column("releases", sa.Column("artist_mappings", _json_type(), nullable=True))
    op.add_column("releases", sa.Column("policy_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("releases", sa.Column("policy_version", sa.String(length=64), nullable=True))

    connection = op.get_bind()
    releases = connection.execute(
        sa.text(
            "SELECT id, artists, artist_name, mapping_spotify, mapping_apple, "
            "profile_email, requires_new_profile FROM releases"
        )
    ).mappings()
    for release in releases:
        artists = release["artists"]
        if isinstance(artists, str):
            try:
                artists = json.loads(artists)
            except json.JSONDecodeError:
                artists = []
        primary = next(
            (
                item.get("name")
                for item in (artists or [])
                if isinstance(item, dict) and item.get("role") == "primary"
            ),
            None,
        ) or release["artist_name"]
        mappings = []
        if primary and any(
            (
                release["mapping_spotify"],
                release["mapping_apple"],
                release["profile_email"],
                release["requires_new_profile"],
            )
        ):
            mappings.append(
                {
                    "artist_name": primary,
                    "requires_new_profile": bool(release["requires_new_profile"]),
                    "profile_email": release["profile_email"],
                    "spotify_url": release["mapping_spotify"],
                    "apple_music_url": release["mapping_apple"],
                }
            )
        update_sql = (
            "UPDATE releases SET artist_mappings = CAST(:value AS JSONB) WHERE id = :id"
            if connection.dialect.name == "postgresql"
            else "UPDATE releases SET artist_mappings = :value WHERE id = :id"
        )
        connection.execute(
            sa.text(update_sql),
            {"value": json.dumps(mappings), "id": release["id"]},
        )
    op.alter_column("releases", "artist_mappings", nullable=False)

    for name, column_type in (
        ("quote_asset", sa.String(length=16)),
        ("quote_network", sa.String(length=64)),
        ("quoted_amount", sa.String(length=64)),
        ("quoted_usd_rate", sa.String(length=64)),
        ("quote_created_at", sa.DateTime()),
        ("quote_expires_at", sa.DateTime()),
        ("stars_amount", sa.Integer()),
        ("invoice_payload", sa.String(length=255)),
        ("provider_charge_id", sa.String(length=255)),
    ):
        op.add_column("transactions", sa.Column(name, column_type, nullable=True))
    op.create_unique_constraint("uq_transactions_invoice_payload", "transactions", ["invoice_payload"])
    op.create_unique_constraint("uq_transactions_provider_charge_id", "transactions", ["provider_charge_id"])


def downgrade():
    op.drop_constraint("uq_transactions_provider_charge_id", "transactions", type_="unique")
    op.drop_constraint("uq_transactions_invoice_payload", "transactions", type_="unique")
    for name in (
        "provider_charge_id",
        "invoice_payload",
        "stars_amount",
        "quote_expires_at",
        "quote_created_at",
        "quoted_usd_rate",
        "quoted_amount",
        "quote_network",
        "quote_asset",
    ):
        op.drop_column("transactions", name)
    op.drop_column("releases", "policy_version")
    op.drop_column("releases", "policy_accepted_at")
    op.drop_column("releases", "artist_mappings")
