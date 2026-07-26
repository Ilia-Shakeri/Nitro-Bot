from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_telegram_user, get_tg_id
from database import get_db
from models import User, Transaction, Release
from schemas import UserOut, TransactionOut, ReleaseOut, LanguageResponse, UserLanguageUpdate
import storage
from user_identity import sync_telegram_profile

router = APIRouter(prefix="/users", tags=["users"])

# Languages the mini-app actually ships; anything else is rejected as bad input.
_SUPPORTED_LANGUAGES = {"en", "fa", "ar", "ru"}


async def _presign_release_cover(release: Release) -> Release:
    if release.cover_url:
        release.cover_url = await storage.presign(release.cover_url)
    return release


def owned_release_statement(release_id: int, tg_id: int):
    return select(Release).where(
        Release.id == release_id,
        Release.user_id == tg_id,
    )


@router.get("/me", response_model=UserOut)
async def get_user(
    telegram_user: dict = Depends(get_telegram_user),
    db: AsyncSession = Depends(get_db),
):
    tg_id = int(telegram_user["id"])
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=tg_id, language_preference="fa", credits=0)
        db.add(user)
    if any(field in telegram_user for field in ("first_name", "last_name", "username")):
        sync_telegram_profile(
            user,
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            username=telegram_user.get("username"),
        )
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
        .where(
            Transaction.user_id == tg_id,
            Transaction.status != "quoted",
        )
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
    releases = result.scalars().all()
    import asyncio
    await asyncio.gather(*[_presign_release_cover(release) for release in releases])
    return releases


@router.get("/me/releases/{release_id}", response_model=ReleaseOut)
async def get_release(
    release_id: int,
    tg_id: int = Depends(get_tg_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(owned_release_statement(release_id, tg_id))
    release = result.scalars().first()
    if not release:
        raise HTTPException(status_code=404, detail="source_release_not_found")
    return await _presign_release_cover(release)
