import logging
import asyncio

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db, AsyncSessionLocal
from models import User, Release, Transaction
from pricing import release_cost
from schemas import ReleaseCreateResponse
import storage
from bot import notify_admin_new_release

logger = logging.getLogger("nitro.releases")

router = APIRouter(prefix="/releases", tags=["releases"])


async def _background_convert_and_notify(
    release_id: int,
    tg_id: int,
    submitter: str,
    audio_bytes_raw: bytes | None,
    cover_bytes_raw: bytes | None,
    existing_audio_key: str | None,
    existing_cover_key: str | None,
    final_song_name: str,
    final_artist_name: str,
    final_producers: str | None,
    final_legal_name: str,
    final_genre: str,
    final_sub_genre: str | None,
    final_release_date: str,
    final_mapping_spotify: str | None,
    final_mapping_apple: str | None,
    final_profile_email: str | None,
    requires_new_profile: bool,
    is_edit: bool,
    copyright_requested: bool,
    total_cost: int,
):
    try:
        wav_bytes = None
        cover_bytes = None
        audio_key_final = existing_audio_key
        cover_key_final = existing_cover_key

        if audio_bytes_raw:
            wav_bytes = await storage.convert_audio_to_wav(audio_bytes_raw)
            audio_key_final = await storage.upload(wav_bytes, f"releases/{tg_id}", "track.wav")
        elif existing_audio_key:
            try:
                wav_bytes = await storage.download(existing_audio_key)
            except Exception:
                logger.exception("Failed to load existing audio for release %s", release_id)

        if cover_bytes_raw:
            cover_bytes, _ = await storage.process_cover(cover_bytes_raw)
            cover_key_final = await storage.upload(cover_bytes, f"releases/{tg_id}", "cover.png")
        elif existing_cover_key:
            try:
                cover_bytes = await storage.download(existing_cover_key)
            except Exception:
                logger.exception("Failed to load existing cover for release %s", release_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Release).where(Release.id == release_id))
            release = result.scalars().first()
            if release:
                if audio_key_final:
                    release.track_url = audio_key_final
                if cover_key_final:
                    release.cover_url = cover_key_final
                await db.commit()

        await notify_admin_new_release(
            release_id=release_id,
            song_name=final_song_name,
            artist_name=final_artist_name,
            producers=final_producers,
            legal_name=final_legal_name,
            genre=final_genre or "",
            sub_genre=final_sub_genre,
            release_date=final_release_date,
            mapping_spotify=final_mapping_spotify,
            mapping_apple=final_mapping_apple,
            requires_new_profile=requires_new_profile,
            profile_email=final_profile_email,
            is_edit=is_edit,
            copyright_requested=copyright_requested,
            cost=total_cost,
            submitter=submitter,
            audio_bytes=wav_bytes,
            audio_filename="track.wav" if wav_bytes else None,
            cover_bytes=cover_bytes,
            cover_filename="cover.png" if cover_bytes else None,
        )
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Release).where(Release.id == release_id))
            release = result.scalars().first()
            if release:
                release.status = "manual_staging"
                await db.commit()
    except Exception:
        logger.exception("Background conversion failed for release %s", release_id)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Release).where(Release.id == release_id))
                release = result.scalars().first()
                user_result = await db.execute(select(User).where(User.telegram_id == tg_id))
                user = user_result.scalars().first()
                if release and release.status != "failed":
                    release.status = "failed"
                    if user:
                        user.credits += total_cost
                    db.add(Transaction(
                        user_id=tg_id,
                        amount=total_cost,
                        status="rollback",
                        payment_method=f"release-{release_id}-refund",
                    ))
                    await db.commit()
        except Exception:
            logger.exception("Failed to mark release %s as failed", release_id)


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    tg_id: int = Depends(get_tg_id),
    song_name: str | None = Form(None),
    artist_name: str | None = Form(None),
    producers: str | None = Form(None),
    legal_name: str | None = Form(None),
    release_date: str | None = Form(None),
    genre: str | None = Form(None),
    sub_genre: str | None = Form(None),
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
    final_sub_genre = sub_genre if sub_genre is not None else (
        source_release.sub_genre if source_release else None
    )

    try:
        datetime.strptime(final_release_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Release date must be YYYY-MM-DD format")

    final_mapping_spotify = mapping_spotify if mapping_spotify is not None else (
        source_release.mapping_spotify if source_release else None
    )
    final_mapping_apple = mapping_apple if mapping_apple is not None else (
        source_release.mapping_apple if source_release else None
    )
    final_profile_email = profile_email.strip() if profile_email else (
        source_release.profile_email if source_release else None
    )

    total_cost = release_cost(is_edit, requires_new_profile, copyright_requested)
    if user.credits < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough credits ({total_cost} required)")

    audio_key = None
    cover_key = None
    audio_bytes_raw = None
    cover_bytes_raw = None

    if audio:
        audio_bytes_raw = await storage.read_audio(audio)
    else:
        audio_key = source_release.track_url if source_release else None

    if cover:
        cover_bytes_raw = await storage.read_image(cover)
    else:
        cover_key = source_release.cover_url if source_release else None

    release = Release(
        user_id=tg_id,
        track_url=audio_key or "",
        cover_url=cover_key or "",
        song_name=final_song_name,
        artist_name=final_artist_name,
        producers=final_producers,
        legal_name=final_legal_name,
        release_date=final_release_date,
        genre=final_genre,
        sub_genre=final_sub_genre,
        mapping_spotify=final_mapping_spotify,
        mapping_apple=final_mapping_apple,
        profile_email=final_profile_email,
        requires_new_profile=requires_new_profile,
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        status="staging",
    )
    user.credits -= total_cost
    db.add(release)
    await db.commit()
    await db.refresh(release)

    submitter = f"@{user.username}" if user.username else f"ID:{tg_id}"

    asyncio.create_task(
        _background_convert_and_notify(
            release_id=release.id,
            tg_id=tg_id,
            submitter=submitter,
            audio_bytes_raw=audio_bytes_raw,
            cover_bytes_raw=cover_bytes_raw,
            existing_audio_key=audio_key,
            existing_cover_key=cover_key,
            final_song_name=final_song_name,
            final_artist_name=final_artist_name,
            final_producers=final_producers,
            final_legal_name=final_legal_name,
            final_genre=final_genre or "",
            final_sub_genre=final_sub_genre,
            final_release_date=final_release_date,
            final_mapping_spotify=final_mapping_spotify,
            final_mapping_apple=final_mapping_apple,
            final_profile_email=final_profile_email,
            requires_new_profile=requires_new_profile,
            is_edit=is_edit,
            copyright_requested=copyright_requested,
            total_cost=total_cost,
        )
    )

    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
