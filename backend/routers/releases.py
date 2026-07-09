import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import AsyncSessionLocal, get_db
from models import User, Release, Transaction
from schemas import ReleaseCreateResponse
import storage
from bot import notify_admin_new_release

logger = logging.getLogger("nitro.releases")

router = APIRouter(prefix="/releases", tags=["releases"])

NEW_RELEASE_COST = 10
EDIT_RELEASE_COST = 2
COPYRIGHT_COST = 1


def _failure_reason(exc: Exception) -> str:
    return str(exc)[:500] or exc.__class__.__name__


async def _background_convert_and_notify(
    release_id: int,
    tg_id: int,
    total_cost: int,
    submitter: str,
    audio_bytes: bytes,
    cover_bytes: bytes,
) -> None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Release).where(Release.id == release_id))
            release = result.scalars().first()
            if not release:
                logger.error("Release %s disappeared before staging finished", release_id)
                return

            wav_bytes = await storage.convert_audio_to_wav(audio_bytes)
            processed_cover, cover_ext = await storage.process_cover(cover_bytes)
            audio_key = await storage.upload(wav_bytes, f"releases/{tg_id}", "track.wav")
            cover_key = await storage.upload(processed_cover, f"releases/{tg_id}", f"cover.{cover_ext}")

            release.track_url = audio_key
            release.cover_url = cover_key
            release.status = "staging"
            release.failure_reason = None
            await db.commit()

            await notify_admin_new_release(
                release_id=release.id,
                song_name=release.song_name,
                artist_name=release.artist_name,
                genre=release.genre or "-",
                release_date=release.release_date,
                cost=total_cost,
                submitter=submitter,
                audio_bytes=wav_bytes,
                audio_filename="track.wav",
                cover_bytes=processed_cover,
                cover_filename=f"cover.{cover_ext}",
            )
        except Exception as exc:
            logger.error("Failed to stage release %s", release_id, exc_info=True)
            await db.rollback()

            result = await db.execute(select(Release).where(Release.id == release_id))
            release = result.scalars().first()
            user_result = await db.execute(select(User).where(User.telegram_id == tg_id))
            user = user_result.scalars().first()

            already_failed = release is not None and release.status == "failed"
            if release:
                release.status = "failed"
                release.failure_reason = _failure_reason(exc)
            if user and not already_failed:
                user.credits += total_cost
                db.add(Transaction(
                    user_id=tg_id,
                    amount=total_cost,
                    status="release_refund",
                    payment_method="rollback",
                    receipt_url=f"release:{release_id}",
                ))
            await db.commit()


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    background_tasks: BackgroundTasks,
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

    base_cost = EDIT_RELEASE_COST if is_edit else NEW_RELEASE_COST
    total_cost = base_cost + (COPYRIGHT_COST if copyright_requested else 0)
    if user.credits < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough credits ({total_cost} required)")

    audio_bytes = await storage.read_audio(audio)
    cover_bytes = await storage.read_image(cover)

    release = Release(
        user_id=tg_id,
        track_url="",
        cover_url="",
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

    submitter = f"@{user.username}" if user.username else f"ID:{tg_id}"
    background_tasks.add_task(
        _background_convert_and_notify,
        release.id,
        tg_id,
        total_cost,
        submitter,
        audio_bytes,
        cover_bytes,
    )
    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
