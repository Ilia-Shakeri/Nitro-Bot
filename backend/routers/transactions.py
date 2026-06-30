import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Transaction
from schemas import ReceiptSubmitResponse
import storage
from bot import notify_admin_new_receipt

logger = logging.getLogger("nitro.transactions")

router = APIRouter(prefix="/transactions", tags=["transactions"])

# card = Blu Bank card-to-card, btc = Bitcoin, usdt = Tether TRC20.
# "tether" kept for backwards compatibility with older clients.
ALLOWED_PAYMENT_METHODS = {"card", "btc", "usdt", "tether"}


@router.post("/receipt", response_model=ReceiptSubmitResponse)
async def submit_receipt(
    tg_id: int = Depends(get_tg_id),
    amount: int = Form(...),
    payment_method: str = Form(...),
    receipt: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    if payment_method not in ALLOWED_PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Allowed: {', '.join(sorted(ALLOWED_PAYMENT_METHODS))}",
        )

    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receipt_bytes = await storage.read_image(receipt, max_mb=5)
    receipt_key = await storage.upload(receipt_bytes, f"receipts/{tg_id}", receipt.filename or "receipt")

    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        payment_method=payment_method,
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
            payment_method=payment_method,
            submitter=submitter,
            receipt_bytes=receipt_bytes,
            receipt_filename=receipt.filename or "receipt.jpg",
        )
    except Exception:
        logger.exception("Failed to notify admin of receipt %s", tx.id)
    return {"status": "ok", "transaction_id": tx.id}
