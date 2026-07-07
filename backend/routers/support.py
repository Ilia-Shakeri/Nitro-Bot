from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from auth import get_tg_id
from database import get_db
from models import User, SupportMessage, SupportTicket, get_naive_utc
from bot import notify_admin_new_ticket
from schemas import OkResponse, SupportTicketOut
from fastapi import HTTPException

router = APIRouter(prefix="/support", tags=["support"])

_MAX_SUBJECT_LEN = 200
_MAX_MESSAGE_LEN = 4000


class TicketCreate(BaseModel):
    subject: str = ""
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

    subject_text = body.subject.strip()[:_MAX_SUBJECT_LEN]
    message_text = body.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(message_text) > _MAX_MESSAGE_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long (max {_MAX_MESSAGE_LEN} characters)",
        )

    ticket = SupportTicket(
        user_id=tg_id,
        subject=subject_text,
        status="open",
        updated_at=get_naive_utc(),
    )
    db.add(ticket)
    await db.flush()
    db.add(SupportMessage(ticket_id=ticket.id, sender="user", message=message_text))
    await db.commit()

    await notify_admin_new_ticket(ticket.id, tg_id, name, username, subject_text, message_text)
    return {"status": "ok"}
