from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Transaction, Release
from schemas import UserOut, TransactionOut, ReleaseOut, LanguageResponse, UserLanguageUpdate

router = APIRouter(prefix="/users", tags=["users"])

# Languages the mini-app actually ships; anything else is rejected as bad input.
_SUPPORTED_LANGUAGES = {"en", "fa"}


@router.get("/me", response_model=UserOut)
async def get_user(tg_id: int = Depends(get_tg_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=tg_id, language_preference="fa", credits=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@router.post("/me/language", response_model=LanguageResponse)
async def update_language(
    body: UserLanguageUpdate,
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    if body.language not in _SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Allowed: {', '.join(sorted(_SUPPORTED_LANGUAGES))}",
        )
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.language_preference = body.language
    await db.commit()
    return {"status": "ok", "language": user.language_preference}


@router.get("/me/transactions", response_model=list[TransactionOut])
async def get_transactions(tg_id: int = Depends(get_tg_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == tg_id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


@router.get("/me/releases", response_model=list[ReleaseOut])
async def get_releases(tg_id: int = Depends(get_tg_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Release)
        .where(Release.user_id == tg_id)
        .order_by(Release.created_at.desc())
    )
    return result.scalars().all()
