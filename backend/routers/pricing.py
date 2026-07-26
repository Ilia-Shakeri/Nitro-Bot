import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User
from pricing import pricing_payload
from schemas import PaymentConfigOut, PricingOut

router = APIRouter(prefix="/pricing", tags=["pricing"])


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


def payment_config_payload(language: str | None) -> dict:
    is_persian = (language or "").split("-")[0] == "fa"
    card_number = os.getenv("PAYMENT_CARD_NUMBER", "").strip()
    card_holder = os.getenv("PAYMENT_CARD_HOLDER", "").strip()
    usdt_address = os.getenv("PAYMENT_USDT_TRC20_ADDRESS", "").strip()
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
    if not card and not usdt:
        raise HTTPException(status_code=503, detail="payment_config_unavailable")
    return {
        "card": card,
        "usdt": usdt,
    }
