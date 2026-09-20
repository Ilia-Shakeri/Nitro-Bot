import asyncio
import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

import storage
from database import AsyncSessionLocal
from models import NotificationOutbox, SupportMessage, SupportTicket, Transaction, User

logger = logging.getLogger("nitro.notification_jobs")
LEASE_SECONDS = max(30, int(os.getenv("NOTIFICATION_JOB_LEASE_SECONDS", "120")))
MAX_ATTEMPTS = max(1, int(os.getenv("NOTIFICATION_JOB_MAX_ATTEMPTS", "5")))
POLL_SECONDS = max(1, int(os.getenv("NOTIFICATION_JOB_POLL_SECONDS", "2")))
_WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue_notification(
    db: AsyncSession,
    *,
    kind: str,
    aggregate_id: str | int,
    idempotency_key: str,
    payload: dict | None = None,
) -> NotificationOutbox:
    job = NotificationOutbox(
        kind=kind,
        aggregate_id=str(aggregate_id),
        idempotency_key=idempotency_key,
        payload=payload or {},
    )
    db.add(job)
    return job


async def _claim_one() -> int | None:
    now = utc_now()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NotificationOutbox)
            .where(
                or_(
                    and_(
                        NotificationOutbox.status.in_(("queued", "retry")),
                        NotificationOutbox.next_attempt_at <= now,
                    ),
                    and_(
                        NotificationOutbox.status == "processing",
                        NotificationOutbox.lease_expires_at < now,
                    ),
                )
            )
            .order_by(NotificationOutbox.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = result.scalars().first()
        if job is None:
            await db.rollback()
            return None
        job.status = "processing"
        job.attempts += 1
        job.lease_owner = _WORKER_ID
        job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        job.updated_at = now
        await db.commit()
        return job.id


async def _send_payment(tx_id: int, payload: dict) -> None:
    from bot import notify_admin_new_receipt

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Transaction, User)
            .join(User, User.telegram_id == Transaction.user_id)
            .where(Transaction.id == tx_id)
        )
        row = result.first()
        if row is None:
            raise RuntimeError("payment_notification_target_missing")
        tx, user = row
        submitter = f"@{user.username}" if user.username else f"ID:{user.telegram_id}"
        receipt_bytes = await storage.download(tx.receipt_url) if tx.receipt_url else None
        await notify_admin_new_receipt(
            tx_id=tx.id,
            amount=tx.amount,
            payment_method=tx.payment_method,
            submitter=submitter,
            receipt_bytes=receipt_bytes,
            receipt_filename=payload.get("receipt_filename"),
            usd_amount_cents=tx.usd_amount_cents,
            toman_amount_cents=tx.toman_amount_cents,
            quote_asset=tx.quote_asset,
            quote_network=tx.quote_network,
            quoted_amount=tx.quoted_amount,
        )


async def _send_ticket(ticket_id: int) -> None:
    from bot import notify_admin_new_ticket

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SupportTicket, User)
            .join(User, User.telegram_id == SupportTicket.user_id)
            .where(SupportTicket.id == ticket_id)
        )
        row = result.first()
        if row is None:
            raise RuntimeError("ticket_notification_target_missing")
        ticket, user = row
        message_result = await db.execute(
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket.id, SupportMessage.sender == "user")
            .order_by(SupportMessage.created_at.asc())
            .limit(1)
        )
        first_message = message_result.scalars().first()
        if first_message is None:
            raise RuntimeError("ticket_message_missing")
        await notify_admin_new_ticket(
            ticket.id,
            user.telegram_id,
            user.first_name or "Unknown",
            f"@{user.username}" if user.username else f"ID:{user.telegram_id}",
            ticket.subject,
            first_message.message,
        )


async def _send_payment_result(tx_id: int) -> None:
    from bot import _TRANSLATIONS, _send_message

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Transaction, User)
            .join(User, User.telegram_id == Transaction.user_id)
            .where(Transaction.id == tx_id)
        )
        row = result.first()
        if row is None:
            raise RuntimeError("payment_result_target_missing")
        tx, user = row
        lang = user.language_preference if user.language_preference in _TRANSLATIONS else "fa"
        key = "tx_approved" if tx.status == "approved" else "tx_rejected"
        if tx.status not in {"approved", "rejected"}:
            raise RuntimeError("payment_result_state_invalid")
        await _send_message(chat_id=user.telegram_id, text=_TRANSLATIONS[lang][key].format(tx.amount))


async def _send_ticket_reply(message_id: int) -> None:
    from bot import _TRANSLATIONS, _send_message

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SupportMessage, SupportTicket, User)
            .join(SupportTicket, SupportTicket.id == SupportMessage.ticket_id)
            .join(User, User.telegram_id == SupportTicket.user_id)
            .where(SupportMessage.id == message_id, SupportMessage.sender == "admin")
        )
        row = result.first()
        if row is None:
            raise RuntimeError("ticket_reply_target_missing")
        support_message, _, user = row
        lang = user.language_preference if user.language_preference in _TRANSLATIONS else "fa"
        await _send_message(
            chat_id=user.telegram_id,
            text=_TRANSLATIONS[lang]["ticket_reply"].format(support_message.message),
        )


async def _process(job_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(NotificationOutbox).where(NotificationOutbox.id == job_id))
        job = result.scalars().first()
        if job is None:
            return
        kind = job.kind
        aggregate_id = int(job.aggregate_id)
        payload = dict(job.payload or {})

    if kind == "payment_receipt":
        await _send_payment(aggregate_id, payload)
    elif kind == "support_ticket":
        await _send_ticket(aggregate_id)
    elif kind == "user_payment_result":
        await _send_payment_result(aggregate_id)
    elif kind == "user_ticket_reply":
        await _send_ticket_reply(aggregate_id)
    else:
        raise RuntimeError("notification_kind_invalid")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NotificationOutbox)
            .where(
                NotificationOutbox.id == job_id,
                NotificationOutbox.status == "processing",
                NotificationOutbox.lease_owner == _WORKER_ID,
            )
            .with_for_update()
        )
        job = result.scalars().first()
        if job is None:
            raise RuntimeError("notification_job_lease_lost")
        job.status = "sent"
        job.lease_owner = None
        job.lease_expires_at = None
        job.last_error = None
        job.updated_at = utc_now()
        await db.commit()


async def _record_failure(job_id: int, error: Exception) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NotificationOutbox)
            .where(NotificationOutbox.id == job_id, NotificationOutbox.lease_owner == _WORKER_ID)
            .with_for_update()
        )
        job = result.scalars().first()
        if job is None:
            await db.rollback()
            return
        job.last_error = f"{type(error).__name__}: {error}"[:2000]
        job.lease_owner = None
        job.lease_expires_at = None
        job.updated_at = utc_now()
        if job.attempts >= MAX_ATTEMPTS:
            job.status = "dead"
        else:
            job.status = "retry"
            job.next_attempt_at = utc_now() + timedelta(seconds=min(300, 2 ** job.attempts))
        await db.commit()


async def run_notification_job_worker() -> None:
    while True:
        job_id = await _claim_one()
        if job_id is None:
            await asyncio.sleep(POLL_SECONDS)
            continue
        try:
            await _process(job_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Notification job %s failed", job_id)
            await _record_failure(job_id, exc)
