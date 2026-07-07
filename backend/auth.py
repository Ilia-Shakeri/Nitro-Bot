import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

_BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SKIP_TELEGRAM_AUTH = os.getenv("SKIP_TELEGRAM_AUTH", "false").lower() == "true"
_DEV_USER_ID = 123_456_789
# Reject initData older than this. Telegram's initData is replayable forever once
# captured, so we bound its lifetime to limit the stolen-token window.
_INIT_DATA_MAX_AGE = int(os.getenv("INIT_DATA_MAX_AGE_SECONDS", str(24 * 3600)))


def _verify(init_data: str) -> dict | None:
    """Return parsed initData dict if HMAC-SHA256 signature is valid and fresh, else None."""
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
    if not hmac.compare_digest(expected, received):
        return None
    # Signature is valid — now enforce freshness to block replay of old captures.
    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError:
        return None
    if _INIT_DATA_MAX_AGE > 0 and (time.time() - auth_date) > _INIT_DATA_MAX_AGE:
        return None
    return parsed


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
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid user data in Telegram auth")
