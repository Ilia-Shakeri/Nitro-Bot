from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Release
from schemas import ReleaseCreateResponse
import storage

router = APIRouter(prefix="/releases", tags=["releases"])


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    tg_id: int = Depends(get_tg_id),
    song_name: str = Form(...),
    artist_name: str = Form(...),
    legal_name: str = Form(...),
    release_date: str = Form(...),
    mapping_spotify: str | None = Form(None),
    mapping_apple: str | None = Form(None),
    requires_new_profile: bool = Form(False),
    is_edit: bool = Form(False),
    copyright_requested: bool = Form(False),
    audio: UploadFile = File(...),
    cover: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    base_cost = 1 if is_edit else 10
    total_cost = base_cost + (2 if copyright_requested else 0)
    if user.credits < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough credits ({total_cost} required)")

    audio_bytes = await storage.read_audio(audio)
    cover_bytes = await storage.read_image(cover)

    audio_key = await storage.upload(audio_bytes, f"releases/{tg_id}", audio.filename or "audio")
    cover_key = await storage.upload(cover_bytes, f"releases/{tg_id}", cover.filename or "cover")

    release = Release(
        user_id=tg_id,
        track_url=audio_key,
        cover_url=cover_key,
        song_name=song_name,
        artist_name=artist_name,
        legal_name=legal_name,
        release_date=release_date,
        mapping_spotify=mapping_spotify,
        mapping_apple=mapping_apple,
        requires_new_profile=requires_new_profile,
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        status="pending",
    )
    user.credits -= total_cost
    db.add(release)
    await db.commit()
    await db.refresh(release)
    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
