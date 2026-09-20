from sqlalchemy.ext.asyncio import AsyncSession

from models import BalanceLedgerEntry


def add_ledger_entry(
    db: AsyncSession,
    *,
    user_id: int,
    amount: int,
    kind: str,
    idempotency_key: str,
    transaction_id: int | None = None,
    release_id: int | None = None,
    details: dict | None = None,
) -> BalanceLedgerEntry:
    if amount == 0:
        raise ValueError("ledger_amount_zero")
    entry = BalanceLedgerEntry(
        user_id=user_id,
        amount=amount,
        kind=kind,
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        release_id=release_id,
        details=details or {},
    )
    db.add(entry)
    return entry
