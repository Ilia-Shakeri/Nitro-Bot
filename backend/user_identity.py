from typing import Protocol


class TelegramProfileRecord(Protocol):
    first_name: str | None
    last_name: str | None
    username: str | None


def clean_telegram_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned[:255] or None


def sync_telegram_profile(
    user: TelegramProfileRecord,
    *,
    first_name: object,
    last_name: object,
    username: object,
) -> None:
    user.first_name = clean_telegram_text(first_name)
    user.last_name = clean_telegram_text(last_name)
    user.username = clean_telegram_text(username)
