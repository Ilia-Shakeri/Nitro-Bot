from typing import Protocol


class StarsTransaction(Protocol):
    user_id: int
    payment_method: str
    status: str
    stars_amount: int | None


def stars_payment_matches(
    transaction: StarsTransaction,
    tg_id: int,
    currency: str,
    total_amount: int,
) -> bool:
    return bool(
        currency == "XTR"
        and transaction.user_id == tg_id
        and transaction.payment_method == "telegram_stars"
        and transaction.status == "pending"
        and transaction.stars_amount == total_amount
    )
