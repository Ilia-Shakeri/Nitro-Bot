"""financial ledger, staff audit, and notification outbox

Revision ID: 015
Revises: 014
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade():
    op.add_column("transactions", sa.Column("submission_id", sa.String(64), nullable=True))
    op.add_column("transactions", sa.Column("receipt_sha256", sa.String(64), nullable=True))
    op.create_index("ix_transactions_submission_id", "transactions", ["submission_id"], unique=True)
    op.create_index("ix_transactions_receipt_sha256", "transactions", ["receipt_sha256"], unique=True)

    op.create_table(
        "balance_ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False, unique=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("release_id", sa.Integer(), sa.ForeignKey("releases.id"), nullable=True),
        sa.Column("details", _json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount != 0", name="ck_balance_ledger_amount_nonzero"),
        sa.CheckConstraint(
            "kind IN ('topup', 'release_charge', 'release_refund', 'referral_reward')",
            name="ck_balance_ledger_kind_allowed",
        ),
    )
    op.create_index("ix_balance_ledger_entries_user_id", "balance_ledger_entries", ["user_id"])
    op.execute(sa.text("""
        INSERT INTO balance_ledger_entries
            (user_id, amount, kind, idempotency_key, transaction_id, details, created_at)
        SELECT user_id, amount, 'topup',
               'transaction:' || CAST(id AS VARCHAR) || ':topup', id,
               json_build_object('payment_method', payment_method), created_at
        FROM transactions
        WHERE status = 'approved'
    """))
    op.execute(sa.text("""
        INSERT INTO balance_ledger_entries
            (user_id, amount, kind, idempotency_key, release_id, details, created_at)
        SELECT user_id, -charged_cost, 'release_charge',
               'release:' || CAST(id AS VARCHAR) || ':charge', id,
               json_build_object('song_name', song_name, 'artist_name', artist_name), created_at
        FROM releases
        WHERE charged_cost > 0
    """))
    op.execute(sa.text("""
        INSERT INTO balance_ledger_entries
            (user_id, amount, kind, idempotency_key, release_id, details, created_at)
        SELECT user_id, charged_cost, 'release_refund',
               'release:' || CAST(id AS VARCHAR) || ':refund', id,
               json_build_object('reason', failure_reason), refunded_at
        FROM releases
        WHERE charged_cost > 0 AND refunded_at IS NOT NULL
    """))

    op.create_table(
        "staff_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(128), nullable=False),
        sa.Column("old_state", sa.String(64), nullable=True),
        sa.Column("new_state", sa.String(64), nullable=True),
        sa.Column("details", _json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_staff_audit_logs_actor_id", "staff_audit_logs", ["actor_id"])

    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("aggregate_id", sa.String(128), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False, unique=True),
        sa.Column("payload", _json_type(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("attempts >= 0", name="ck_notification_outbox_attempts_nonnegative"),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'retry', 'sent', 'dead')",
            name="ck_notification_outbox_status_allowed",
        ),
        sa.CheckConstraint(
            "kind IN ('payment_receipt', 'support_ticket', 'user_payment_result', 'user_ticket_reply')",
            name="ck_notification_outbox_kind_allowed",
        ),
    )
    op.create_index(
        "ix_notification_outbox_claim",
        "notification_outbox",
        ["status", "next_attempt_at", "lease_expires_at"],
    )


def downgrade():
    op.drop_index("ix_notification_outbox_claim", table_name="notification_outbox")
    op.drop_table("notification_outbox")
    op.drop_index("ix_staff_audit_logs_actor_id", table_name="staff_audit_logs")
    op.drop_table("staff_audit_logs")
    op.drop_index("ix_balance_ledger_entries_user_id", table_name="balance_ledger_entries")
    op.drop_table("balance_ledger_entries")
    op.drop_index("ix_transactions_receipt_sha256", table_name="transactions")
    op.drop_index("ix_transactions_submission_id", table_name="transactions")
    op.drop_column("transactions", "receipt_sha256")
    op.drop_column("transactions", "submission_id")
