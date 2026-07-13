import logging
import os
import time

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Transaction, Release
from pricing import release_cost
from schemas import LedgerOut, ReceiptSubmitResponse, UsdtRateOut
import storage
from bot import notify_admin_new_receipt

logger = logging.getLogger("nitro.transactions")

router = APIRouter(prefix="/transactions", tags=["transactions"])

# card = Blu Bank card-to-card, btc = Bitcoin, usdt = Tether TRC20.
# "tether" kept for backwards compatibility with older clients.
ALLOWED_PAYMENT_METHODS = {"card", "btc", "usdt", "tether"}

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


@router.get("/usdt-rate", response_model=UsdtRateOut)
async def usdt_rate():
    now = time.time()
    if _rate_cache["rate"] > 0 and (now - _rate_cache["ts"]) < _RATE_TTL_SECONDS:
        return {"rate_toman": int(_rate_cache["rate"]), "cached": True}
    try:
        rate = await _fetch_usdt_toman()
        _rate_cache["rate"] = float(rate)
        _rate_cache["ts"] = now
        return {"rate_toman": rate, "cached": False}
    except Exception:
        logger.exception("Failed to fetch USDT/Toman rate")
        # Serve a stale cached value if we have one, else the manual fallback.
        if _rate_cache["rate"] > 0:
            return {"rate_toman": int(_rate_cache["rate"]), "cached": True}
        if _RATE_FALLBACK > 0:
            return {"rate_toman": _RATE_FALLBACK, "cached": True}
        raise HTTPException(status_code=503, detail="Exchange rate unavailable")


@router.get("/ledger", response_model=list[LedgerOut])
async def get_ledger(tg_id: int = Depends(get_tg_id), db: AsyncSession = Depends(get_db)):
    tx_result = await db.execute(select(Transaction).where(Transaction.user_id == tg_id))
    release_result = await db.execute(select(Release).where(Release.user_id == tg_id))

    entries = [
        {
            "id": f"tx-{tx.id}",
            "amount": tx.amount,
            "direction": "credit",
            "title": f"Nitro top-up ({tx.payment_method})",
            "status": tx.status,
            "created_at": tx.created_at,
        }
        for tx in tx_result.scalars().all()
    ]
    for release in release_result.scalars().all():
        cost = release_cost(release.is_edit, release.requires_new_profile, release.copyright_requested)
        entries.append(
            {
                "id": f"release-{release.id}",
                "amount": cost,
                "direction": "debit",
                "title": f"{release.song_name} - {release.artist_name}",
                "status": release.status,
                "created_at": release.created_at,
            }
        )
    return sorted(entries, key=lambda item: item["created_at"], reverse=True)


@router.post("/receipt", response_model=ReceiptSubmitResponse)
async def submit_receipt(
    tg_id: int = Depends(get_tg_id),
    amount: int = Form(...),
    payment_method: str = Form(...),
    receipt: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    if amount < 3:
        raise HTTPException(status_code=400, detail="Minimum charge amount is 3")
    normalized_payment_method = "usdt" if payment_method == "tether" else payment_method
    if normalized_payment_method not in ALLOWED_PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Allowed: {', '.join(sorted(ALLOWED_PAYMENT_METHODS))}",
        )

    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (user.language_preference or "").split("-")[0] != "fa" and normalized_payment_method != "usdt":
        raise HTTPException(status_code=400, detail="Only USDT payments are available for non-Persian users")

    if normalized_payment_method != "usdt" and receipt is None:
        raise HTTPException(status_code=400, detail="Receipt image is required for card payments")

    receipt_bytes = None
    receipt_key = None
    if receipt is not None:
        receipt_bytes = await storage.read_image(receipt, max_mb=5)
        receipt_key = await storage.upload(receipt_bytes, f"receipts/{tg_id}", receipt.filename or "receipt")

    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        payment_method=normalized_payment_method,
        status="pending",
        receipt_url=receipt_key,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    # Forward the actual receipt image (uploaded by bytes — MinIO's internal URL is
    # not reachable by Telegram's servers) plus submitter details to the admin group.
    # Transaction is already persisted; a Telegram failure must not 500 the
    # request, or the user would resubmit and create a duplicate receipt.
    submitter = f"@{user.username}" if user.username else f"ID:{tg_id}"
    try:
        await notify_admin_new_receipt(
            tx_id=tx.id,
            amount=amount,
            payment_method=normalized_payment_method,
            submitter=submitter,
            receipt_bytes=receipt_bytes,
            receipt_filename=receipt.filename if receipt else None,
        )
    except Exception:
        logger.exception("Failed to notify admin of receipt %s", tx.id)
    return {"status": "ok", "transaction_id": tx.id}
