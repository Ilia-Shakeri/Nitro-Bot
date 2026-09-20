import hashlib
import logging
import os
import re
import secrets
import time
from datetime import datetime, timezone

import httpx
from aiogram.types import LabeledPrice
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import BalanceLedgerEntry, User, Transaction
from notification_jobs import enqueue_notification
from payment_config import load_payment_settings
from payment_methods import (
    ALLOWED_PAYMENT_METHODS,
    MANUAL_CRYPTO_METHODS,
    normalize_payment_method,
    receipt_is_required,
)
from payment_quotes import create_payment_quote
from pricing import PRICING
from schemas import (
    CryptoQuoteOut,
    LedgerOut,
    ReceiptSubmitResponse,
    StarsInvoiceOut,
    UsdtRateOut,
)
import storage
from bot import bot

logger = logging.getLogger("nitro.transactions")

router = APIRouter(prefix="/transactions", tags=["transactions"])
_FRIENDLY_LEDGER_METHODS = {
    "card",
    "usdt",
    "tether",
    "btc",
    "bnb",
    "usdt_bnb",
    "telegram_stars",
}

_NOBITEX_ORDERBOOK_URL = os.getenv("NOBITEX_ORDERBOOK_URL") or \
    "https://api.nobitex.ir/v2/orderbook/USDTIRT"
_WALLEX_MARKETS_URL = os.getenv("WALLEX_MARKETS_URL") or \
    "https://api.wallex.ir/v1/markets"
_RATE_TTL_SECONDS = 60
# Optional manual fallback (Toman) used only when the exchange is unreachable
# and nothing is cached yet. 0 disables it (the endpoint then returns 503).
try:
    _RATE_FALLBACK = int(os.getenv("USDT_TOMAN_FALLBACK") or "0")
except ValueError:
    _RATE_FALLBACK = 0
_rate_cache: dict[str, float] = {"rate": 0.0, "ts": 0.0}


async def _delete_receipt_key(key: str | None) -> None:
    if not key:
        return
    try:
        await storage.delete(key)
    except Exception:
        logger.exception("Failed to delete unused receipt object")


def _read_first_price(levels: list) -> int:
    if not levels:
        raise ValueError("orderbook has no price levels")
    first = levels[0]
    raw = first[0] if isinstance(first, list | tuple) else first.get("price")
    price = int(float(raw))
    if price <= 0:
        raise ValueError("exchange returned a non-positive rate")
    return price


async def _fetch_nobitex_usdt_irt(client: httpx.AsyncClient) -> int:
    resp = await client.get(_NOBITEX_ORDERBOOK_URL)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") not in {None, "ok"}:
        raise ValueError("nobitex returned a failed status")
    return _read_first_price(data.get("asks") or data.get("bids") or [])


def _find_wallex_usdt_price(payload: object) -> int:
    markets = payload.get("result", {}).get("symbols") if isinstance(payload, dict) else None
    if markets is None and isinstance(payload, dict):
        markets = payload.get("symbols") or payload.get("markets") or payload.get("result")
    if isinstance(markets, dict):
        iterable = markets.values()
    elif isinstance(markets, list):
        iterable = markets
    else:
        raise ValueError("wallex response has no markets")

    for market in iterable:
        if not isinstance(market, dict):
            continue
        symbol = str(market.get("symbol") or market.get("name") or "").upper()
        base = str(market.get("baseAsset") or market.get("baseCurrency") or "").upper()
        quote = str(market.get("quoteAsset") or market.get("quoteCurrency") or "").upper()
        if symbol in {"USDTIRT", "USDTTMN"} or (base == "USDT" and quote in {"IRT", "TMN"}):
            raw = (
                market.get("stats", {}).get("lastPrice")
                or market.get("stats", {}).get("bidPrice")
                or market.get("lastPrice")
                or market.get("bidPrice")
                or market.get("price")
            )
            price = int(float(raw))
            if price > 0:
                return price
    raise ValueError("wallex USDT/IRT market not found")


async def _fetch_wallex_usdt_irt(client: httpx.AsyncClient) -> int:
    resp = await client.get(_WALLEX_MARKETS_URL)
    resp.raise_for_status()
    return _find_wallex_usdt_price(resp.json())


async def _fetch_usdt_toman() -> int:
    """Fetch the latest USDT price in Toman from Nobitex, then Wallex."""
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            return await _fetch_nobitex_usdt_irt(client)
        except Exception:
            logger.exception("Nobitex USDT/IRT fetch failed; trying Wallex")
            try:
                return await _fetch_wallex_usdt_irt(client)
            except Exception:
                logger.exception("Wallex USDT/IRT fetch also failed")
                raise


async def _current_usdt_rate() -> tuple[int, bool]:
    now = time.time()
    if _rate_cache["rate"] > 0 and (now - _rate_cache["ts"]) < _RATE_TTL_SECONDS:
        return int(_rate_cache["rate"]), True
    try:
        rate = await _fetch_usdt_toman()
        _rate_cache["rate"] = float(rate)
        _rate_cache["ts"] = now
        return rate, False
    except Exception:
        logger.exception("Failed to fetch USDT/Toman rate")
        # Serve a stale cached value if we have one, else the manual fallback.
        if _rate_cache["rate"] > 0:
            return int(_rate_cache["rate"]), True
        if _RATE_FALLBACK > 0:
            return _RATE_FALLBACK, True
        raise HTTPException(status_code=503, detail="Exchange rate unavailable")


@router.get("/usdt-rate", response_model=UsdtRateOut)
async def usdt_rate(_: int = Depends(get_tg_id)):
    rate, cached = await _current_usdt_rate()
    return {"rate_toman": rate, "cached": cached}


def _method_is_configured(payment_method: str) -> bool:
    settings = load_payment_settings()
    return {
        "card": bool(settings.payment_card_number and settings.payment_card_holder),
        "usdt": bool(settings.payment_usdt_trc20_address),
        "btc": bool(settings.payment_btc_address),
        "bnb": bool(settings.payment_bnb_bep20_address),
        "usdt_bnb": bool(settings.payment_usdt_bep20_address),
        "telegram_stars": settings.telegram_stars_per_nitro > 0,
    }.get(payment_method, False)


@router.get("/quote", response_model=CryptoQuoteOut)
async def payment_quote(
    amount: int = Query(...),
    payment_method: str = Query(...),
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    normalized = normalize_payment_method(payment_method)
    if normalized not in MANUAL_CRYPTO_METHODS:
        raise HTTPException(status_code=400, detail="payment_method_invalid")
    if not _method_is_configured(normalized):
        raise HTTPException(status_code=503, detail="payment_method_unavailable")
    try:
        quote = await create_payment_quote(normalized, amount)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except (httpx.HTTPError, ArithmeticError):
        logger.exception("Crypto quote failed for %s", normalized)
        raise HTTPException(status_code=503, detail="payment_quote_unavailable") from None
    user_result = await db.execute(select(User).where(User.telegram_id == tg_id))
    if not user_result.scalars().first():
        raise HTTPException(status_code=404, detail="user_not_found")
    await db.execute(
        delete(Transaction).where(
            Transaction.user_id == tg_id,
            Transaction.status == "quoted",
            Transaction.quote_expires_at < quote.quoted_at,
        )
    )
    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        payment_method=normalized,
        status="quoted",
        usd_amount_cents=amount * PRICING.nitro_usd_price_cents,
        quote_asset=quote.asset,
        quote_network=quote.network,
        quoted_amount=format(quote.amount, "f"),
        quoted_usd_rate=format(quote.usd_rate, "f"),
        quote_created_at=quote.quoted_at,
        quote_expires_at=quote.expires_at,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return {"transaction_id": tx.id, **quote.payload()}


@router.post("/stars-invoice", response_model=StarsInvoiceOut)
async def create_stars_invoice(
    amount: int = Form(...),
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    settings = load_payment_settings()
    if amount < PRICING.minimum_topup_nitro:
        raise HTTPException(status_code=400, detail="minimum_topup")
    if settings.telegram_stars_per_nitro <= 0:
        raise HTTPException(status_code=503, detail="payment_method_unavailable")
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="user_not_found")

    stars_amount = amount * settings.telegram_stars_per_nitro
    payload = f"nitro:{secrets.token_urlsafe(32)}"
    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        payment_method="telegram_stars",
        status="pending",
        usd_amount_cents=amount * PRICING.nitro_usd_price_cents,
        stars_amount=stars_amount,
        invoice_payload=payload,
        quote_asset="XTR",
        quote_network="Telegram",
        quoted_amount=str(stars_amount),
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    try:
        invoice_url = await bot.create_invoice_link(
            title="Nitro top-up",
            description=f"{amount} Nitro",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=f"{amount} Nitro", amount=stars_amount)],
        )
    except Exception:
        tx.status = "failed"
        await db.commit()
        logger.exception("Stars invoice creation failed for transaction %s", tx.id)
        raise HTTPException(status_code=503, detail="invoice_creation_failed") from None
    return {
        "transaction_id": tx.id,
        "invoice_url": invoice_url,
        "stars_amount": stars_amount,
    }


@router.get("/ledger", response_model=list[LedgerOut])
async def get_ledger(tg_id: int = Depends(get_tg_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BalanceLedgerEntry)
        .where(BalanceLedgerEntry.user_id == tg_id)
        .order_by(BalanceLedgerEntry.created_at.desc())
    )
    entries = []
    for entry in result.scalars().all():
        method = str((entry.details or {}).get("payment_method", ""))
        if entry.kind == "release_charge":
            title_key = "ledger_release"
            title = f"{(entry.details or {}).get('song_name', 'Release')} - {(entry.details or {}).get('artist_name', '')}"
        elif entry.kind == "release_refund":
            title_key = "ledger_refund"
            title = "Release refund"
        elif entry.kind == "referral_reward":
            title_key = "ledger_referral_reward"
            title = "Referral reward"
        else:
            title_key = f"ledger_topup_{method}" if method in _FRIENDLY_LEDGER_METHODS else "ledger_topup"
            title = f"Nitro top-up ({method})" if method else "Nitro top-up"
        entries.append({
            "id": f"ledger-{entry.id}",
            "amount": abs(entry.amount),
            "direction": "credit" if entry.amount > 0 else "debit",
            "title": title,
            "title_key": title_key,
            "title_params": {
                str(key): value if isinstance(value, (str, int)) else ""
                for key, value in (entry.details or {}).items()
            },
            "status": "completed",
            "created_at": entry.created_at,
        })
    return entries


@router.post("/receipt", response_model=ReceiptSubmitResponse)
async def submit_receipt(
    tg_id: int = Depends(get_tg_id),
    amount: int = Form(...),
    payment_method: str = Form(...),
    submission_id: str = Form(...),
    quote_transaction_id: int | None = Form(None),
    receipt: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    if amount < PRICING.minimum_topup_nitro:
        raise HTTPException(status_code=400, detail="minimum_topup")
    normalized_submission_id = submission_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", normalized_submission_id):
        raise HTTPException(status_code=400, detail="submission_id_invalid")
    normalized_payment_method = normalize_payment_method(payment_method)
    if normalized_payment_method not in ALLOWED_PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail="payment_method_invalid",
        )

    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    if normalized_payment_method == "telegram_stars":
        raise HTTPException(status_code=400, detail="stars_invoice_required")
    if normalized_payment_method == "card" and (
        user.language_preference or ""
    ).split("-")[0] != "fa":
        raise HTTPException(status_code=400, detail="card_only_for_persian")
    if not _method_is_configured(normalized_payment_method):
        raise HTTPException(status_code=503, detail="payment_method_unavailable")

    existing_result = await db.execute(
        select(Transaction).where(Transaction.submission_id == normalized_submission_id)
    )
    existing = existing_result.scalars().first()
    if existing:
        if (
            existing.user_id != tg_id
            or existing.amount != amount
            or existing.payment_method != normalized_payment_method
        ):
            raise HTTPException(status_code=409, detail="submission_id_conflict")
        return {"status": "ok", "transaction_id": existing.id}

    if receipt_is_required(normalized_payment_method) and receipt is None:
        raise HTTPException(status_code=400, detail="receipt_required")

    usd_amount_cents = amount * PRICING.nitro_usd_price_cents
    toman_amount_cents = None
    tx = None
    if normalized_payment_method == "card":
        rate, _ = await _current_usdt_rate()
        toman_amount_cents = usd_amount_cents * rate
    elif normalized_payment_method in MANUAL_CRYPTO_METHODS:
        if quote_transaction_id is None:
            raise HTTPException(status_code=400, detail="payment_quote_required")
        quote_result = await db.execute(
            select(Transaction)
            .where(
                Transaction.id == quote_transaction_id,
                Transaction.user_id == tg_id,
            )
            .with_for_update()
        )
        tx = quote_result.scalars().first()
        if (
            not tx
            or tx.status != "quoted"
            or tx.payment_method != normalized_payment_method
            or tx.amount != amount
            or not tx.quote_expires_at
            or tx.quote_expires_at
            < datetime.now(timezone.utc).replace(tzinfo=None)
        ):
            raise HTTPException(status_code=400, detail="payment_quote_expired")

    receipt_bytes = await storage.read_image(receipt, max_mb=5) if receipt else None
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest() if receipt_bytes else None
    if receipt_sha256:
        proof_result = await db.execute(
            select(Transaction.id).where(Transaction.receipt_sha256 == receipt_sha256)
        )
        if proof_result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="receipt_already_submitted")
    receipt_key = None
    if receipt_bytes is not None:
        receipt_key = await storage.upload(
            receipt_bytes,
            f"receipts/{tg_id}/{normalized_submission_id}",
            receipt.filename or "receipt",
        )

    try:
        if tx is None:
            tx = Transaction(
                user_id=tg_id,
                amount=amount,
                payment_method=normalized_payment_method,
                status="pending",
                receipt_url=receipt_key,
                receipt_sha256=receipt_sha256,
                submission_id=normalized_submission_id,
                usd_amount_cents=usd_amount_cents,
                toman_amount_cents=toman_amount_cents,
            )
            db.add(tx)
            await db.flush()
        else:
            tx.status = "pending"
            tx.receipt_url = receipt_key
            tx.receipt_sha256 = receipt_sha256
            tx.submission_id = normalized_submission_id
        enqueue_notification(
            db,
            kind="payment_receipt",
            aggregate_id=tx.id,
            idempotency_key=f"payment-receipt:{tx.id}:submitted",
            payload={"receipt_filename": receipt.filename if receipt else None},
        )
        await db.commit()
        await db.refresh(tx)
    except IntegrityError:
        await db.rollback()
        await _delete_receipt_key(receipt_key)
        duplicate_result = await db.execute(
            select(Transaction).where(Transaction.submission_id == normalized_submission_id)
        )
        duplicate = duplicate_result.scalars().first()
        if duplicate and duplicate.user_id == tg_id:
            return {"status": "ok", "transaction_id": duplicate.id}
        raise HTTPException(status_code=409, detail="receipt_already_submitted") from None
    except Exception:
        await db.rollback()
        await _delete_receipt_key(receipt_key)
        raise
    return {"status": "ok", "transaction_id": tx.id}
