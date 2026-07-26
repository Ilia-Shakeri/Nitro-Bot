import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User
from payment_config import (
    PaymentSettings,
    load_payment_settings,
    normalized_card_number,
)
from pricing import pricing_payload
from schemas import PaymentConfigOut, PricingOut

router = APIRouter(prefix="/pricing", tags=["pricing"])
logger = logging.getLogger("nitro.payment_config")


@router.get("", response_model=PricingOut)
async def get_pricing(_: int = Depends(get_tg_id)):
    return pricing_payload()


@router.get("/payment-config", response_model=PaymentConfigOut)
async def get_payment_config(
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return payment_config_payload(user.language_preference)


def payment_config_payload(
    language: str | None,
    settings: PaymentSettings | None = None,
) -> dict:
    is_persian = (language or "").split("-")[0] == "fa"
    payment_settings = settings or load_payment_settings()
    card_number = normalized_card_number(payment_settings.payment_card_number)
    card_holder = payment_settings.payment_card_holder
    usdt_address = payment_settings.payment_usdt_trc20_address
    btc_address = payment_settings.payment_btc_address
    bnb_address = payment_settings.payment_bnb_bep20_address
    usdt_bnb_address = payment_settings.payment_usdt_bep20_address
    card = (
        {"number": card_number, "holder": card_holder}
        if is_persian and card_number and card_holder
        else None
    )
    usdt = (
        {"network": "TRON (TRC20)", "asset": "USDT", "address": usdt_address}
        if usdt_address
        else None
    )
    btc = (
        {"network": "Bitcoin", "asset": "BTC", "address": btc_address}
        if btc_address
        else None
    )
    bnb = (
        {"network": "BNB Smart Chain (BEP20)", "asset": "BNB", "address": bnb_address}
        if bnb_address
        else None
    )
    usdt_bnb = (
        {
            "network": "BNB Smart Chain (BEP20)",
            "asset": "USDT",
            "address": usdt_bnb_address,
        }
        if usdt_bnb_address
        else None
    )
    telegram_stars = (
        {
            "network": "Telegram",
            "asset": "XTR",
            "stars_per_nitro": payment_settings.telegram_stars_per_nitro,
        }
        if payment_settings.telegram_stars_per_nitro > 0
        else None
    )
    if not any((card, usdt, btc, bnb, usdt_bnb, telegram_stars)):
        raise HTTPException(status_code=503, detail="payment_config_unavailable")
    return {
        "card": card,
        "usdt": usdt,
        "btc": btc,
        "bnb": bnb,
        "usdt_bnb": usdt_bnb,
        "telegram_stars": telegram_stars,
    }
