from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ledger import add_ledger_entry
from models import Release, Transaction, User


def user_for_update_statement(telegram_id: int) -> Select:
    return select(User).where(User.telegram_id == telegram_id).with_for_update()


def refund_is_due(refunded_at: datetime | None) -> bool:
    return refunded_at is None


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def fail_release_and_refund(
    db: AsyncSession,
    release_id: int,
    reason: str,
    *,
    allowed_statuses: set[str] | None = None,
) -> bool:
    release_result = await db.execute(
        select(Release).where(Release.id == release_id).with_for_update()
    )
    release = release_result.scalars().first()
    if release is None:
        await db.rollback()
        return False
    if allowed_statuses is not None and release.status not in allowed_statuses:
        await db.rollback()
        raise ValueError("release_status_transition_invalid")

    release.status = "failed"
    release.failure_reason = reason[:255]
    if not refund_is_due(release.refunded_at):
        await db.commit()
        return False

    user_result = await db.execute(user_for_update_statement(release.user_id))
    user = user_result.scalars().first()
    if user is None:
        await db.rollback()
        raise RuntimeError("release_user_missing_during_refund")

    release.refunded_at = utc_now()
    if release.charged_cost > 0:
        user.credits += release.charged_cost
        refund_tx = Transaction(
            user_id=release.user_id,
            amount=release.charged_cost,
            status="rollback",
            payment_method=f"release-{release.id}-refund",
        )
        db.add(refund_tx)
        await db.flush()
        add_ledger_entry(
            db,
            user_id=release.user_id,
            amount=release.charged_cost,
            kind="release_refund",
            idempotency_key=f"release:{release.id}:refund",
            transaction_id=refund_tx.id,
            release_id=release.id,
            details={"reason": release.failure_reason},
        )
    await db.commit()
    return True
