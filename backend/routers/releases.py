import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import User, Release
from pricing import release_cost
from schemas import ReleaseCreateResponse
import storage
from bot import notify_admin_new_release

logger = logging.getLogger("nitro.releases")

router = APIRouter(prefix="/releases", tags=["releases"])


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    tg_id: int = Depends(get_tg_id),
    song_name: str | None = Form(None),
    artist_name: str | None = Form(None),
    producers: str | None = Form(None),
    legal_name: str | None = Form(None),
    release_date: str | None = Form(None),
    genre: str | None = Form(None),
    mapping_spotify: str | None = Form(None),
    mapping_apple: str | None = Form(None),
    profile_email: str | None = Form(None),
    edited_release_id: int | None = Form(None),
    requires_new_profile: bool = Form(False),
    is_edit: bool = Form(False),
    copyright_requested: bool = Form(False),
    audio: UploadFile | None = File(None),
    cover: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    source_release = None
    if is_edit:
        if edited_release_id is None:
            raise HTTPException(status_code=400, detail="Edited release id is required")
        source_result = await db.execute(
            select(Release).where(Release.id == edited_release_id, Release.user_id == tg_id)
        )
        source_release = source_result.scalars().first()
        if not source_release:
            raise HTTPException(status_code=404, detail="Source release not found")
    elif not all([song_name, artist_name, legal_name, release_date, genre, audio, cover]):
        raise HTTPException(status_code=400, detail="Please fill all required fields")
    if requires_new_profile and not (profile_email or "").strip():
        raise HTTPException(status_code=400, detail="Profile email is required.")

    final_song_name = song_name or source_release.song_name
    final_artist_name = artist_name or source_release.artist_name
    final_producers = producers if producers is not None else (
        source_release.producers if source_release else None
    )
    final_legal_name = legal_name or source_release.legal_name
    final_release_date = release_date or source_release.release_date
    final_genre = genre or source_release.genre
    final_mapping_spotify = mapping_spotify if mapping_spotify is not None else (
        source_release.mapping_spotify if source_release else None
    )
    final_mapping_apple = mapping_apple if mapping_apple is not None else (
        source_release.mapping_apple if source_release else None
    )

    total_cost = release_cost(is_edit, requires_new_profile, copyright_requested)
    if user.credits < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough credits ({total_cost} required)")

    wav_bytes = None
    cover_bytes = None
    cover_ext = None
    if audio:
        audio_bytes = await storage.read_audio(audio)
        wav_bytes = await storage.convert_audio_to_wav(audio_bytes)
        audio_key = await storage.upload(wav_bytes, f"releases/{tg_id}", "track.wav")
    else:
        audio_key = source_release.track_url
    if cover:
        raw_cover_bytes = await storage.read_image(cover)
        cover_bytes, cover_ext = await storage.process_cover(raw_cover_bytes)
        cover_key = await storage.upload(cover_bytes, f"releases/{tg_id}", f"cover.{cover_ext}")
    else:
        cover_key = source_release.cover_url

    release = Release(
        user_id=tg_id,
        track_url=audio_key,
        cover_url=cover_key,
        song_name=final_song_name,
        artist_name=final_artist_name,
        producers=final_producers,
        legal_name=final_legal_name,
        release_date=final_release_date,
        genre=final_genre,
        mapping_spotify=final_mapping_spotify,
        mapping_apple=final_mapping_apple,
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
            song_name=final_song_name,
            artist_name=final_artist_name,
            producers=final_producers,
            genre=final_genre or "",
            release_date=final_release_date,
            cost=total_cost,
            submitter=submitter,
            audio_bytes=wav_bytes,
            audio_filename="track.wav" if wav_bytes else None,
            cover_bytes=cover_bytes,
            cover_filename=f"cover.{cover_ext}" if cover_bytes and cover_ext else None,
        )
    except Exception:
        logger.exception("Failed to notify admin of release %s", release.id)
    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
