import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Release
from schemas import ReleaseCreateResponse
import storage
from bot import notify_admin_new_release

logger = logging.getLogger("nitro.releases")

router = APIRouter(prefix="/releases", tags=["releases"])


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    tg_id: int = Depends(get_tg_id),
    song_name: str = Form(...),
    artist_name: str = Form(...),
    legal_name: str = Form(...),
    release_date: str = Form(...),
    genre: str = Form(...),
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

    # Media processing in-process (no n8n): WAV for the worker, square >=3000px cover.
    wav_bytes = await storage.convert_audio_to_wav(audio_bytes)
    cover_bytes, cover_ext = await storage.process_cover(cover_bytes)

    audio_key = await storage.upload(wav_bytes, f"releases/{tg_id}", "track.wav")
    cover_key = await storage.upload(cover_bytes, f"releases/{tg_id}", f"cover.{cover_ext}")

    release = Release(
        user_id=tg_id,
        track_url=audio_key,
        cover_url=cover_key,
        song_name=song_name,
        artist_name=artist_name,
        legal_name=legal_name,
        release_date=release_date,
        genre=genre,
        mapping_spotify=mapping_spotify,
        mapping_apple=mapping_apple,
        requires_new_profile=requires_new_profile,
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        # Staging phase: 'staging' is intentionally NOT 'pending', so the
        # DMB-automation worker (which polls status == 'pending') never picks it up.
        status="staging",
    )
    user.credits -= total_cost
    db.add(release)
    await db.commit()
    await db.refresh(release)

    # Send the staged release to the admin Order topic for manual review.
    # The DB is already committed (credits deducted), so a Telegram failure must
    # NOT surface as an error — that would make the user retry and pay twice.
    submitter = f"@{user.username}" if user.username else f"ID:{tg_id}"
    try:
        await notify_admin_new_release(
            release_id=release.id,
            song_name=song_name,
            artist_name=artist_name,
            genre=genre,
            release_date=release_date,
            cost=total_cost,
            submitter=submitter,
            cover_bytes=cover_bytes,
            cover_filename=f"cover.{cover_ext}",
        )
    except Exception:
        logger.exception("Failed to notify admin of release %s", release.id)
    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
