import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

import auth
from routers.users import get_release, owned_release_statement
from schemas import UserOut
from user_identity import sync_telegram_profile


def _signed_init_data(user: dict, *, auth_date: int | None = None) -> str:
    values = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "test-query",
        "user": json.dumps(user, separators=(",", ":")),
    }
    check = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret = hmac.new(b"WebAppData", auth._BOT_TOKEN.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


@pytest.mark.asyncio
async def test_validated_telegram_identity_contains_profile_fields():
    identity = await auth.get_telegram_user(
        _signed_init_data({
            "id": 42,
            "first_name": "Mina",
            "last_name": "Azadi",
            "username": "mina_music",
        })
    )
    assert identity == {
        "id": 42,
        "first_name": "Mina",
        "last_name": "Azadi",
        "username": "mina_music",
    }


def test_telegram_identity_rejects_auth_date_too_far_in_future():
    init_data = _signed_init_data(
        {"id": 42, "first_name": "Mina"},
        auth_date=int(time.time()) + auth._INIT_DATA_FUTURE_SKEW + 60,
    )
    assert auth._verify(init_data) is None


def test_user_response_exposes_telegram_profile_fields():
    user = UserOut(
        telegram_id=42,
        username="mina_music",
        first_name="Mina",
        last_name="Azadi",
        language_preference="fa",
        credits=8,
        referral_points=0,
    )
    assert user.model_dump()["last_name"] == "Azadi"


def test_telegram_profile_sync_normalizes_all_name_fields():
    user = SimpleNamespace(first_name=None, last_name=None, username=None)
    sync_telegram_profile(
        user,
        first_name="  Mina ",
        last_name=" Azadi  ",
        username=" mina_music ",
    )
    assert (user.first_name, user.last_name, user.username) == (
        "Mina",
        "Azadi",
        "mina_music",
    )


def test_release_detail_query_checks_owner():
    statement = owned_release_statement(7, 42)
    compiled = statement.compile(dialect=postgresql.dialect())
    assert "releases.id" in str(compiled)
    assert "releases.user_id" in str(compiled)
    assert set(compiled.params.values()) == {7, 42}


class _EmptyScalars:
    @staticmethod
    def first():
        return None


class _EmptyResult:
    @staticmethod
    def scalars():
        return _EmptyScalars()


class _EmptySession:
    @staticmethod
    async def execute(_statement):
        return _EmptyResult()


@pytest.mark.asyncio
async def test_release_detail_hides_missing_or_foreign_release():
    with pytest.raises(HTTPException) as exc:
        await get_release(7, tg_id=42, db=_EmptySession())
    assert exc.value.status_code == 404
    assert exc.value.detail == "source_release_not_found"
