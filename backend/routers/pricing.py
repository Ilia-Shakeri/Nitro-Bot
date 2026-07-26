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
    card = (
        {"number": card_number, "holder": card_holder}
        if is_persian and card_number and card_holder
        else None
    )
    usdt = (
        {"network": "USDT (TRC20)", "address": usdt_address}
        if usdt_address
        else None
    )
    missing = []
    if not usdt_address:
        missing.append("PAYMENT_USDT_TRC20_ADDRESS")
    if is_persian and not card_number:
        missing.append("PAYMENT_CARD_NUMBER")
    if is_persian and not card_holder:
        missing.append("PAYMENT_CARD_HOLDER")
    if missing:
        logger.warning(
            "Payment destinations incomplete for language %s; missing: %s",
            (language or "unknown").split("-")[0],
            ", ".join(missing),
        )
    if not card and not usdt:
        raise HTTPException(status_code=503, detail="payment_config_unavailable")
    return {
        "card": card,
        "usdt": usdt,
    }
