from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_UP

import httpx

from payment_config import PaymentSettings, load_payment_settings
from pricing import PRICING

QUOTE_TTL_SECONDS = 120
_MARKET_CACHE_SECONDS = 30
_ASSET_CONFIG = {
    "btc": ("BTC", "Bitcoin", "bitcoin", Decimal("0.00000001")),
    "bnb": ("BNB", "BNB Smart Chain (BEP20)", "binancecoin", Decimal("0.00000001")),
    "usdt": ("USDT", "TRON (TRC20)", None, Decimal("0.01")),
    "usdt_bnb": ("USDT", "BNB Smart Chain (BEP20)", None, Decimal("0.01")),
}
_market_cache: dict[str, tuple[Decimal, float]] = {}
_market_lock = asyncio.Lock()


@dataclass(frozen=True)
class PaymentQuote:
    payment_method: str
    asset: str
    network: str
    amount: Decimal
    usd_rate: Decimal
    quoted_at: datetime
    expires_at: datetime

    def payload(self) -> dict[str, str | datetime]:
        return {
            "payment_method": self.payment_method,
            "asset": self.asset,
            "network": self.network,
            "amount": format(self.amount, "f"),
            "usd_rate": format(self.usd_rate, "f"),
            "quoted_at": self.quoted_at,
            "expires_at": self.expires_at,
        }


async def _fetch_usd_rate(
    provider_id: str,
    settings: PaymentSettings,
    client: httpx.AsyncClient | None = None,
) -> Decimal:
    cached = _market_cache.get(provider_id)
    now = time.monotonic()
    if cached and now - cached[1] < _MARKET_CACHE_SECONDS:
        return cached[0]

    async with _market_lock:
        cached = _market_cache.get(provider_id)
        now = time.monotonic()
        if cached and now - cached[1] < _MARKET_CACHE_SECONDS:
            return cached[0]
        owns_client = client is None
        market_client = client or httpx.AsyncClient(timeout=5.0)
        try:
            response = await market_client.get(
                settings.crypto_quote_url,
                params={"ids": provider_id, "vs_currencies": "usd"},
            )
            response.raise_for_status()
            raw_rate = response.json().get(provider_id, {}).get("usd")
            rate = Decimal(str(raw_rate))
            if not rate.is_finite() or rate <= 0:
                raise ValueError("quote_provider_invalid")
        finally:
            if owns_client:
                await market_client.aclose()
        _market_cache[provider_id] = (rate, time.monotonic())
        return rate


async def create_payment_quote(
    payment_method: str,
    nitro_amount: int,
    *,
    settings: PaymentSettings | None = None,
    client: httpx.AsyncClient | None = None,
) -> PaymentQuote:
    if payment_method not in _ASSET_CONFIG:
        raise ValueError("payment_method_invalid")
    if nitro_amount < PRICING.minimum_topup_nitro:
        raise ValueError("minimum_topup")
    asset, network, provider_id, precision = _ASSET_CONFIG[payment_method]
    usd_total = (
        Decimal(nitro_amount) * Decimal(PRICING.nitro_usd_price_cents) / Decimal(100)
    )
    payment_settings = settings or load_payment_settings()
    usd_rate = (
        Decimal("1")
        if provider_id is None
        else await _fetch_usd_rate(provider_id, payment_settings, client)
    )
    asset_amount = (usd_total / usd_rate).quantize(precision, rounding=ROUND_UP)
    quoted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return PaymentQuote(
        payment_method=payment_method,
        asset=asset,
        network=network,
        amount=asset_amount,
        usd_rate=usd_rate,
        quoted_at=quoted_at,
        expires_at=quoted_at + timedelta(seconds=QUOTE_TTL_SECONDS),
    )
