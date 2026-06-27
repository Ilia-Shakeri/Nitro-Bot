import hashlib
import hmac
import json
import os
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

_BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SKIP_TELEGRAM_AUTH = os.getenv("SKIP_TELEGRAM_AUTH", "false").lower() == "true"
_DEV_USER_ID = 123_456_789


def _verify(init_data: str) -> dict | None:
    """Return parsed initData dict if HMAC-SHA256 signature is valid, else None."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except Exception:
        return None
    received = parsed.pop("hash", None)
    if not received:
        return None
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", _BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return parsed if hmac.compare_digest(expected, received) else None


async def get_tg_id(x_telegram_init_data: str = Header(None)) -> int:
    """FastAPI dependency: validates Telegram initData header, returns verified user ID."""
    if SKIP_TELEGRAM_AUTH:
        return _DEV_USER_ID
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram authentication")
    parsed = _verify(x_telegram_init_data)
    if not parsed:
        raise HTTPException(status_code=401, detail="Invalid Telegram authentication")
    try:
        user_data = json.loads(parsed.get("user", "{}"))
        return int(user_data["id"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user data in Telegram auth")
