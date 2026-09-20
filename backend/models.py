from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import backref, declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

def get_naive_utc():
    # Strip the timezone info to create a naive UTC datetime
    # This prevents the asyncpg offset mismatch with TIMESTAMP WITHOUT TIME ZONE
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("credits >= 0", name="ck_users_credits_nonnegative"),)

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_preference = Column(String, default="fa")
    credits = Column(Integer, nullable=False, default=0)
    referred_by = Column(BigInteger, nullable=True)
    referral_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=get_naive_utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    payment_method = Column(String, default="card") 
    receipt_url = Column(String, nullable=True)
    usd_amount_cents = Column(Integer, nullable=False, default=0)
    toman_amount_cents = Column(BigInteger, nullable=True)
    quote_asset = Column(String(16), nullable=True)
    quote_network = Column(String(64), nullable=True)
    quoted_amount = Column(String(64), nullable=True)
    quoted_usd_rate = Column(String(64), nullable=True)
    quote_created_at = Column(DateTime, nullable=True)
    quote_expires_at = Column(DateTime, nullable=True)
    stars_amount = Column(Integer, nullable=True)
    invoice_payload = Column(String(255), nullable=True, unique=True)
    provider_charge_id = Column(String(255), nullable=True, unique=True)
    submission_id = Column(String(64), nullable=True, unique=True, index=True)
    receipt_sha256 = Column(String(64), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=get_naive_utc)

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject = Column(String, default="")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=get_naive_utc)
    updated_at = Column(DateTime, default=get_naive_utc)

    user = relationship("User", backref="support_tickets")

class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_naive_utc)

    ticket = relationship("SupportTicket", backref=backref("messages", order_by="SupportMessage.created_at"))

class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (
        CheckConstraint("charged_cost >= 0", name="ck_releases_charged_cost_nonnegative"),
        CheckConstraint("dmb_attempts >= 0", name="ck_releases_dmb_attempts_nonnegative"),
        CheckConstraint(
            "status IN ('pending', 'staging', 'notification_pending', 'manual_staging', 'processing', 'dmb_verification_required', 'completed', 'failed')",
            name="ck_releases_status_allowed",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    track_url = Column(String, nullable=False)
    cover_url = Column(String, nullable=False)
    song_name = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    artists = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    producers = Column(Text, nullable=True)
    legal_name = Column(String, nullable=False)
    legal_names = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    release_date = Column(Date, nullable=False)
    is_rerelease = Column(Boolean, nullable=False, default=False)
    original_release_date = Column(Date, nullable=True)
    genre = Column(String, nullable=True)
    sub_genre = Column(String, nullable=True)
    mapping_spotify = Column(String, nullable=True)
    mapping_apple = Column(String, nullable=True)
    profile_email = Column(String, nullable=True)
    requires_new_profile = Column(Boolean, nullable=False, default=False)
    artist_mappings = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    policy_accepted_at = Column(DateTime, nullable=True)
    policy_version = Column(String(64), nullable=True)
    
    # Financial and Logic Flags
    is_edit = Column(Boolean, nullable=False, default=False)
    copyright_requested = Column(Boolean, nullable=False, default=False)
    explicit_content = Column(Boolean, nullable=False, default=False)
    charged_cost = Column(Integer, nullable=False, default=0)
    submission_id = Column(String(64), nullable=True, unique=True, index=True)
    refunded_at = Column(DateTime, nullable=True)
    failure_reason = Column(String(255), nullable=True)
    source_release_id = Column(Integer, ForeignKey("releases.id"), nullable=True)
    source_dmb_release_id = Column(String(128), nullable=True)
    edit_diff = Column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
    dmb_release_id = Column(String(128), nullable=True)
    dmb_ean_upc = Column(String(32), nullable=True)
    dmb_isrcs = Column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    dmb_submission_started_at = Column(DateTime, nullable=True)
    dmb_submitted_at = Column(DateTime, nullable=True)
    dmb_evidence_path = Column(String(512), nullable=True)
    dmb_submission_fingerprint = Column(String(64), nullable=True)
    dmb_last_error = Column(Text, nullable=True)
    dmb_attempts = Column(Integer, nullable=False, default=0)
    dmb_lease_owner = Column(String(128), nullable=True)
    dmb_lease_expires_at = Column(DateTime, nullable=True)
    dmb_reviewed_by = Column(String(128), nullable=True)
    dmb_reviewed_at = Column(DateTime, nullable=True)
    
    # State tracking for the Selenium Bot worker
    status = Column(String, default="pending") 
    created_at = Column(DateTime, default=get_naive_utc)

    user = relationship("User", backref="releases", foreign_keys=[user_id])
    source_release = relationship("Release", remote_side=[id], foreign_keys=[source_release_id])


class ReleaseJob(Base):
    __tablename__ = "release_jobs"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="ck_release_jobs_attempts_nonnegative"),
        CheckConstraint("phase IN ('media', 'notify')", name="ck_release_jobs_phase_allowed"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'retry', 'completed', 'dead')",
            name="ck_release_jobs_status_allowed",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    release_id = Column(
        Integer,
        ForeignKey("releases.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    phase = Column(String(32), nullable=False, default="media")
    status = Column(String(32), nullable=False, default="queued")
    source_audio_key = Column(String, nullable=False)
    source_cover_key = Column(String, nullable=False)
    convert_audio = Column(Boolean, nullable=False, default=False)
    convert_cover = Column(Boolean, nullable=False, default=False)
    attempts = Column(Integer, nullable=False, default=0)
    lease_owner = Column(String(128), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    next_attempt_at = Column(DateTime, nullable=False, default=get_naive_utc)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=get_naive_utc)
    updated_at = Column(DateTime, nullable=False, default=get_naive_utc)

    release = relationship("Release", backref=backref("processing_job", uselist=False))


class BalanceLedgerEntry(Base):
    __tablename__ = "balance_ledger_entries"
    __table_args__ = (
        CheckConstraint("amount != 0", name="ck_balance_ledger_amount_nonzero"),
        CheckConstraint(
            "kind IN ('topup', 'release_charge', 'release_refund', 'referral_reward')",
            name="ck_balance_ledger_kind_allowed",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    kind = Column(String(32), nullable=False)
    idempotency_key = Column(String(160), nullable=False, unique=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    release_id = Column(Integer, ForeignKey("releases.id"), nullable=True)
    details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=get_naive_utc)


class StaffAuditLog(Base):
    __tablename__ = "staff_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(64), nullable=False)
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(128), nullable=False)
    old_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=True)
    details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=get_naive_utc)


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="ck_notification_outbox_attempts_nonnegative"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'retry', 'sent', 'dead')",
            name="ck_notification_outbox_status_allowed",
        ),
        CheckConstraint(
            "kind IN ('payment_receipt', 'support_ticket', 'user_payment_result', 'user_ticket_reply')",
            name="ck_notification_outbox_kind_allowed",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(32), nullable=False)
    aggregate_id = Column(String(128), nullable=False)
    idempotency_key = Column(String(160), nullable=False, unique=True)
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="queued")
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=False, default=get_naive_utc)
    lease_owner = Column(String(128), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=get_naive_utc)
    updated_at = Column(DateTime, nullable=False, default=get_naive_utc)
