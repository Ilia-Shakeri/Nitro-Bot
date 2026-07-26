import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from bot import notify_admin_new_release
from database import AsyncSessionLocal, get_db
from models import Release, Transaction, User
from pricing import has_sufficient_credits, release_cost
from release_validation import (
    ReleaseValidationError,
    legacy_artist_name,
    normalize_artists,
    normalize_names,
    normalize_required_names,
    validate_release_dates,
)
from release_service import refund_is_due, user_for_update_statement
from schemas import ReleaseCreateResponse
import storage

logger = logging.getLogger("nitro.releases")
router = APIRouter(prefix="/releases", tags=["releases"])
_background_tasks: set[asyncio.Task[None]] = set()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _refund_failed_release(release_id: int, tg_id: int) -> bool:
    async with AsyncSessionLocal() as db:
        release_result = await db.execute(
            select(Release).where(Release.id == release_id).with_for_update()
        )
        release = release_result.scalars().first()
        if not release or not refund_is_due(release.refunded_at):
            await db.rollback()
            return False

        user_result = await db.execute(
            user_for_update_statement(tg_id)
        )
        user = user_result.scalars().first()
        release.status = "failed"
        release.refunded_at = _utc_now()
        if user and release.charged_cost > 0:
            user.credits += release.charged_cost
            db.add(
                Transaction(
                    user_id=tg_id,
                    amount=release.charged_cost,
                    status="rollback",
                    payment_method=f"release-{release_id}-refund",
                )
            )
        await db.commit()
        return True


async def _background_convert_and_notify(
    *,
    release_id: int,
    tg_id: int,
    submitter: str,
    audio_bytes_raw: bytes | None,
    cover_bytes_raw: bytes | None,
    existing_audio_key: str | None,
    existing_cover_key: str | None,
) -> None:
    try:
        wav_bytes = None
        cover_bytes = None
        audio_key_final = existing_audio_key
        cover_key_final = existing_cover_key

        if audio_bytes_raw:
            wav_bytes = await storage.convert_audio_to_wav(audio_bytes_raw)
            audio_key_final = await storage.upload(
                wav_bytes, f"releases/{tg_id}/{release_id}", "track.wav"
            )
        elif existing_audio_key:
            wav_bytes = await storage.download(existing_audio_key)

        if cover_bytes_raw:
            cover_bytes, _ = await storage.process_cover(cover_bytes_raw)
            cover_key_final = await storage.upload(
                cover_bytes, f"releases/{tg_id}/{release_id}", "cover.png"
            )
        elif existing_cover_key:
            cover_bytes = await storage.download(existing_cover_key)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Release).where(Release.id == release_id))
            release = result.scalars().first()
            if not release:
                raise RuntimeError("release_missing_during_processing")
            if audio_key_final:
                release.track_url = audio_key_final
            if cover_key_final:
                release.cover_url = cover_key_final
            release.status = "manual_staging"
            await db.commit()

            await notify_admin_new_release(
                submitter_tg_id=tg_id,
                release_id=release.id,
                song_name=release.song_name,
                artists=release.artists,
                producers=normalize_names(release.producers, "producers"),
                legal_names=release.legal_names,
                genre=release.genre or "",
                sub_genre=release.sub_genre,
                release_date=release.release_date.isoformat(),
                is_rerelease=release.is_rerelease,
                original_release_date=(
                    release.original_release_date.isoformat()
                    if release.original_release_date
                    else None
                ),
                mapping_spotify=release.mapping_spotify,
                mapping_apple=release.mapping_apple,
                requires_new_profile=release.requires_new_profile,
                profile_email=release.profile_email,
                is_edit=release.is_edit,
                copyright_requested=release.copyright_requested,
                cost=release.charged_cost,
                submitter=submitter,
                audio_bytes=wav_bytes,
                audio_filename="track.wav" if wav_bytes else None,
                cover_bytes=cover_bytes,
                cover_filename="cover.png" if cover_bytes else None,
            )
    except Exception:
        logger.exception("Background conversion failed for release %s", release_id)
        try:
            await _refund_failed_release(release_id, tg_id)
        except Exception:
            logger.exception("Failed to refund release %s", release_id)


@router.post("", response_model=ReleaseCreateResponse)
async def create_release(
    tg_id: int = Depends(get_tg_id),
    song_name: str | None = Form(None),
    artists: str | None = Form(None),
    artist_name: str | None = Form(None),
    producers: str | None = Form(None),
    legal_names: str | None = Form(None),
    legal_name: str | None = Form(None),
    release_date: str | None = Form(None),
    is_rerelease: bool | None = Form(None),
    original_release_date: str | None = Form(None),
    genre: str | None = Form(None),
    sub_genre: str | None = Form(None),
    mapping_spotify: str | None = Form(None),
    mapping_apple: str | None = Form(None),
    profile_email: str | None = Form(None),
    edited_release_id: int | None = Form(None),
    submission_id: str | None = Form(None),
    requires_new_profile: bool | None = Form(None),
    is_edit: bool = Form(False),
    copyright_requested: bool = Form(False),
    audio: UploadFile | None = File(None),
    cover: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    normalized_submission_id = (submission_id or "").strip() or None
    if not normalized_submission_id or len(normalized_submission_id) > 64:
        raise HTTPException(status_code=400, detail="submission_id_invalid")

    if normalized_submission_id:
        duplicate_result = await db.execute(
            select(Release).where(Release.submission_id == normalized_submission_id)
        )
        duplicate = duplicate_result.scalars().first()
        if duplicate:
            if duplicate.user_id != tg_id:
                raise HTTPException(status_code=409, detail="submission_id_conflict")
            user_result = await db.execute(select(User).where(User.telegram_id == tg_id))
            user = user_result.scalars().first()
            return {
                "status": "ok",
                "release_id": duplicate.id,
                "credits_left": user.credits if user else 0,
                "cost_deducted": duplicate.charged_cost,
            }

    source_release = None
    if is_edit:
        if edited_release_id is None:
            raise HTTPException(status_code=400, detail="edited_release_id_required")
        source_result = await db.execute(
            select(Release).where(
                Release.id == edited_release_id,
                Release.user_id == tg_id,
            )
        )
        source_release = source_result.scalars().first()
        if not source_release:
            raise HTTPException(status_code=404, detail="source_release_not_found")

    if not is_edit and not all((song_name, release_date, genre, audio, cover)):
        raise HTTPException(status_code=400, detail="required_fields_missing")

    final_song_name = (song_name or (source_release.song_name if source_release else "")).strip()
    final_genre = (genre or (source_release.genre if source_release else "") or "").strip()
    if not final_song_name or not final_genre:
        raise HTTPException(status_code=400, detail="required_fields_missing")

    try:
        if artists is not None:
            final_artists = normalize_artists(artists)
        elif artist_name and artist_name.strip():
            final_artists = normalize_artists(
                [{"name": artist_name, "role": "primary"}]
            )
        elif source_release:
            final_artists = normalize_artists(source_release.artists)
        else:
            raise ReleaseValidationError("artists_required")

        if legal_names is not None:
            final_legal_names = normalize_names(legal_names, "legal_names")
        elif legal_name and legal_name.strip():
            final_legal_names = normalize_names([legal_name], "legal_names")
        elif source_release:
            final_legal_names = normalize_names(source_release.legal_names, "legal_names")
        else:
            raise ReleaseValidationError("legal_names_required")
        if not final_legal_names:
            raise ReleaseValidationError("legal_names_required")

        final_producer_names = (
            normalize_required_names(producers, "producers")
            if producers is not None
            else normalize_required_names(source_release.producers, "producers")
            if source_release
            else normalize_required_names(None, "producers")
        )

        final_is_rerelease = (
            is_rerelease
            if is_rerelease is not None
            else source_release.is_rerelease
            if source_release
            else False
        )
        release_date_value = (
            release_date
            if release_date is not None
            else source_release.release_date
            if source_release
            else None
        )
        original_date_value = (
            original_release_date
            if original_release_date is not None
            else source_release.original_release_date
            if source_release and final_is_rerelease
            else None
        )
        unchanged_historical = bool(
            source_release
            and final_is_rerelease == source_release.is_rerelease
            and str(release_date_value) == source_release.release_date.isoformat()
        )
        final_release_date, final_original_release_date = validate_release_dates(
            release_date=release_date_value,
            is_rerelease=final_is_rerelease,
            original_release_date=original_date_value,
            allow_unchanged_historical=unchanged_historical,
        )
    except ReleaseValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    final_requires_new_profile = (
        bool(requires_new_profile)
        if requires_new_profile is not None
        else bool(source_release.requires_new_profile) if source_release else False
    )
    final_profile_email = (
        profile_email.strip()
        if profile_email
        else source_release.profile_email if source_release else None
    )
    if final_requires_new_profile and not final_profile_email:
        raise HTTPException(status_code=400, detail="profile_email_required")

    final_mapping_spotify = (
        mapping_spotify
        if mapping_spotify is not None
        else source_release.mapping_spotify if source_release else None
    )
    final_mapping_apple = (
        mapping_apple
        if mapping_apple is not None
        else source_release.mapping_apple if source_release else None
    )
    final_sub_genre = (
        sub_genre
        if sub_genre is not None
        else source_release.sub_genre if source_release else None
    )

    audio_bytes_raw = await storage.read_audio(audio) if audio else None
    cover_bytes_raw = await storage.read_image(cover) if cover else None
    audio_key = source_release.track_url if source_release and not audio else None
    cover_key = source_release.cover_url if source_release and not cover else None
    if not audio_bytes_raw and not audio_key:
        raise HTTPException(status_code=400, detail="audio_required")
    if not cover_bytes_raw and not cover_key:
        raise HTTPException(status_code=400, detail="cover_required")

    total_cost = release_cost(is_edit, copyright_requested)
    user_result = await db.execute(
        user_for_update_statement(tg_id)
    )
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    if normalized_submission_id:
        duplicate_result = await db.execute(
            select(Release).where(Release.submission_id == normalized_submission_id)
        )
        duplicate = duplicate_result.scalars().first()
        if duplicate:
            if duplicate.user_id != tg_id:
                raise HTTPException(status_code=409, detail="submission_id_conflict")
            await db.rollback()
            return {
                "status": "ok",
                "release_id": duplicate.id,
                "credits_left": user.credits,
                "cost_deducted": duplicate.charged_cost,
            }

    if not has_sufficient_credits(user.credits, total_cost):
        raise HTTPException(status_code=400, detail="insufficient_credits")

    release = Release(
        user_id=tg_id,
        track_url=audio_key or "",
        cover_url=cover_key or "",
        song_name=final_song_name,
        artist_name=legacy_artist_name(final_artists),
        artists=final_artists,
        producers=json.dumps(final_producer_names, ensure_ascii=False),
        legal_name=final_legal_names[0],
        legal_names=final_legal_names,
        release_date=final_release_date,
        is_rerelease=final_is_rerelease,
        original_release_date=final_original_release_date,
        genre=final_genre,
        sub_genre=final_sub_genre,
        mapping_spotify=final_mapping_spotify,
        mapping_apple=final_mapping_apple,
        profile_email=final_profile_email,
        requires_new_profile=final_requires_new_profile,
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        charged_cost=total_cost,
        submission_id=normalized_submission_id,
        status="staging",
    )
    user.credits -= total_cost
    db.add(release)
    await db.commit()
    await db.refresh(release)

    submitter = f"@{user.username}" if user.username else f"ID:{tg_id}"
    background_task = asyncio.create_task(
        _background_convert_and_notify(
            release_id=release.id,
            tg_id=tg_id,
            submitter=submitter,
            audio_bytes_raw=audio_bytes_raw,
            cover_bytes_raw=cover_bytes_raw,
            existing_audio_key=audio_key,
            existing_cover_key=cover_key,
        )
    )
    _background_tasks.add(background_task)
    background_task.add_done_callback(_background_tasks.discard)
    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
