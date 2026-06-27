from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Transaction
from schemas import ReceiptSubmitResponse
import storage
from bot import notify_admin_new_receipt

router = APIRouter(prefix="/transactions", tags=["transactions"])


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
    if payment_method not in ("card", "tether"):
        raise HTTPException(status_code=400, detail="Invalid payment method. Allowed: card, tether")

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

    presigned_url = await storage.presign(receipt_key)
    await notify_admin_new_receipt(tx.id, amount, payment_method, presigned_url)
    return {"status": "ok", "transaction_id": tx.id}
