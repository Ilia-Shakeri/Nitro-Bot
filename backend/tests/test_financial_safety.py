import os
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "123456:test-token")

from bot import _staff_action_allowed
from ledger import add_ledger_entry
from models import BalanceLedgerEntry, NotificationOutbox, StaffAuditLog
from notification_jobs import enqueue_notification


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)


def test_ledger_entry_keeps_signed_amount_and_unique_key():
    db = FakeSession()
    entry = add_ledger_entry(
        db,
        user_id=10,
        amount=-3,
        kind="release_charge",
        idempotency_key="release:7:charge",
        release_id=7,
    )
    assert isinstance(entry, BalanceLedgerEntry)
    assert entry.amount == -3
    assert entry.idempotency_key == "release:7:charge"
    assert db.added == [entry]


def test_ledger_rejects_zero_amount():
    db = FakeSession()
    try:
        add_ledger_entry(
            db,
            user_id=10,
            amount=0,
            kind="topup",
            idempotency_key="bad",
        )
    except ValueError as exc:
        assert str(exc) == "ledger_amount_zero"
    else:
        raise AssertionError("zero ledger amount accepted")


def test_outbox_enqueue_has_idempotency_key():
    db = FakeSession()
    job = enqueue_notification(
        db,
        kind="support_ticket",
        aggregate_id=9,
        idempotency_key="support-ticket:9:created",
    )
    assert isinstance(job, NotificationOutbox)
    assert job.aggregate_id == "9"
    assert job.idempotency_key == "support-ticket:9:created"
    assert db.added == [job]


def test_financial_tables_expose_audit_fields():
    assert "idempotency_key" in BalanceLedgerEntry.__table__.columns
    assert "actor_id" in StaffAuditLog.__table__.columns
    assert "lease_expires_at" in NotificationOutbox.__table__.columns


def test_staff_action_needs_group_actor_and_topic(monkeypatch):
    import bot

    monkeypatch.setattr(bot, "ADMIN_GROUP_ID", "-1001")
    monkeypatch.setattr(bot, "MANAGER_IDS", {42})
    message = SimpleNamespace(
        chat=SimpleNamespace(id=-1001),
        message_thread_id=8,
    )
    assert _staff_action_allowed(message, 42, 8)
    assert not _staff_action_allowed(message, 41, 8)
    assert not _staff_action_allowed(message, 42, 9)
