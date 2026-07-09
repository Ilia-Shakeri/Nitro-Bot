from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from auth import get_tg_id
from database import get_db
from models import User, SupportMessage, SupportTicket, get_naive_utc
from bot import notify_admin_new_ticket
from schemas import OkResponse, SupportTicketOut

router = APIRouter(prefix="/support", tags=["support"])


class TicketCreate(BaseModel):
    subject: str
    message: str


@router.get("/tickets", response_model=list[SupportTicketOut])
async def list_tickets(
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SupportTicket)
        .options(selectinload(SupportTicket.messages))
        .where(SupportTicket.user_id == tg_id)
        .order_by(SupportTicket.created_at.desc())
    )
    return result.scalars().all()


@router.post("/tickets", response_model=OkResponse)
async def create_ticket(
    body: TicketCreate,
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    username = f"@{user.username}" if user and user.username else f"ID:{tg_id}"
    name = user.first_name or "Unknown" if user else "Unknown"
    subject = body.subject.strip()
    message = body.message.strip()
    if not subject or not message:
        raise HTTPException(status_code=400, detail="Subject and message are required")

    ticket = SupportTicket(
        user_id=tg_id,
        subject=subject,
        status="open",
        updated_at=get_naive_utc(),
    )
    db.add(ticket)
    await db.flush()
    db.add(SupportMessage(ticket_id=ticket.id, sender="user", message=message))
    await db.commit()

    await notify_admin_new_ticket(ticket.id, tg_id, name, username, subject, message)
    return {"status": "ok"}
