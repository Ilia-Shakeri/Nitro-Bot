from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User
from bot import notify_admin_new_ticket
from schemas import OkResponse

router = APIRouter(prefix="/support", tags=["support"])


class TicketCreate(BaseModel):
    subject: str = ""
    message: str


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

    await notify_admin_new_ticket(tg_id, name, username, body.subject, body.message)
    return {"status": "ok"}
