"""DMB reporter and safe retry states

Revision ID: 018
Revises: 017
"""

from alembic import op


revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_releases_status_allowed", "releases", type_="check")
    op.create_check_constraint(
        "ck_releases_status_allowed",
        "releases",
        "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'dmb_retry_waiting', 'dmb_verification_required', 'dmb_recovery_requested', 'completed', 'failed')",
    )
    op.drop_constraint(
        "ck_notification_outbox_kind_allowed",
        "notification_outbox",
        type_="check",
    )
    op.create_check_constraint(
        "ck_notification_outbox_kind_allowed",
        "notification_outbox",
        "kind IN ('payment_receipt', 'support_ticket', 'user_payment_result', 'user_ticket_reply', 'dmb_success', 'dmb_error', 'dmb_review')",
    )


def downgrade():
    op.execute(
        "UPDATE releases SET status = 'dmb_verification_required' "
        "WHERE status = 'dmb_recovery_requested'"
    )
    op.execute(
        "UPDATE releases SET status = 'manual_staging' "
        "WHERE status = 'dmb_retry_waiting'"
    )
    op.execute(
        "DELETE FROM notification_outbox "
        "WHERE kind IN ('dmb_success', 'dmb_error', 'dmb_review')"
    )
    op.drop_constraint(
        "ck_notification_outbox_kind_allowed",
        "notification_outbox",
        type_="check",
    )
    op.create_check_constraint(
        "ck_notification_outbox_kind_allowed",
        "notification_outbox",
        "kind IN ('payment_receipt', 'support_ticket', 'user_payment_result', 'user_ticket_reply')",
    )
    op.drop_constraint("ck_releases_status_allowed", "releases", type_="check")
    op.create_check_constraint(
        "ck_releases_status_allowed",
        "releases",
        "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'dmb_verification_required', 'completed', 'failed')",
    )
