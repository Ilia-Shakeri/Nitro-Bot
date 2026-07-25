import os

from fastapi import APIRouter, Depends, HTTPException

from auth import get_tg_id
from pricing import pricing_payload
from schemas import PaymentConfigOut, PricingOut

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("", response_model=PricingOut)
async def get_pricing(_: int = Depends(get_tg_id)):
    return pricing_payload()


@router.get("/payment-config", response_model=PaymentConfigOut)
async def get_payment_config(_: int = Depends(get_tg_id)):
    card_number = os.getenv("PAYMENT_CARD_NUMBER", "").strip()
    card_holder = os.getenv("PAYMENT_CARD_HOLDER", "").strip()
    btc_address = os.getenv("PAYMENT_BTC_ADDRESS", "").strip()
    usdt_address = os.getenv("PAYMENT_USDT_TRC20_ADDRESS", "").strip()
    if not any((card_number, btc_address, usdt_address)):
        raise HTTPException(status_code=503, detail="payment_config_unavailable")
    return {
        "card": (
            {"number": card_number, "holder": card_holder}
            if card_number and card_holder
            else None
        ),
        "btc": (
            {"network": "Bitcoin (BTC)", "address": btc_address}
            if btc_address
            else None
        ),
        "usdt": (
            {"network": "USDT (TRC20)", "address": usdt_address}
            if usdt_address
            else None
        ),
    }
