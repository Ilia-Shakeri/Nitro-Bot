from datetime import datetime

from sqlalchemy import Select, select

from models import User


def user_for_update_statement(telegram_id: int) -> Select:
    return select(User).where(User.telegram_id == telegram_id).with_for_update()


def refund_is_due(refunded_at: datetime | None) -> bool:
    return refunded_at is None
