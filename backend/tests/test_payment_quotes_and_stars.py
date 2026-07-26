from decimal import Decimal

import httpx
import pytest

from models import Transaction
from payment_config import PaymentSettings
from payment_quotes import create_payment_quote
from payment_stars import stars_payment_matches


@pytest.mark.asyncio
async def test_usdt_quote_uses_exact_nitro_usd_value():
    quote = await create_payment_quote("usdt", 3, settings=PaymentSettings())
    assert quote.amount == Decimal("2.40")
    assert quote.usd_rate == Decimal("1")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "provider_id", "rate", "expected"),
    [
        ("btc", "bitcoin", 60_000, Decimal("0.00004000")),
        ("bnb", "binancecoin", 600, Decimal("0.00400000")),
    ],
)
async def test_market_quote_uses_decimal_and_rounds_up(
    method,
    provider_id,
    rate,
    expected,
):
    async def handler(request: httpx.Request):
        assert request.url.params["ids"] == provider_id
        return httpx.Response(200, json={provider_id: {"usd": rate}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        quote = await create_payment_quote(
            method,
            3,
            settings=PaymentSettings(crypto_quote_url="https://quote.test"),
            client=client,
        )
    assert quote.amount == expected


def test_stars_payment_validation_checks_every_authoritative_value():
    tx = Transaction(
        user_id=123,
        amount=3,
        payment_method="telegram_stars",
        status="pending",
        stars_amount=12,
    )
    assert stars_payment_matches(tx, 123, "XTR", 12)
    assert not stars_payment_matches(tx, 124, "XTR", 12)
    assert not stars_payment_matches(tx, 123, "USD", 12)
    assert not stars_payment_matches(tx, 123, "XTR", 13)
    tx.status = "approved"
    assert not stars_payment_matches(tx, 123, "XTR", 12)
