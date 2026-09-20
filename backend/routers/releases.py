import json
import logging
import os
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import get_tg_id
from database import get_db
from models import Release, ReleaseJob, User
from ledger import add_ledger_entry
from pricing import has_sufficient_credits, release_cost
from release_validation import (
    ReleaseValidationError,
    legacy_artist_name,
    normalize_artist_mappings,
    normalize_artists,
    normalize_english_text,
    normalize_names,
    normalize_required_names,
    normalize_submission_id,
    validate_genre,
    validate_notice_payload_size,
    validate_policy_acceptance,
    validate_release_dates,
)
from release_service import user_for_update_statement
from schemas import ReleaseCreateResponse
import storage

logger = logging.getLogger("nitro.releases")
router = APIRouter(prefix="/releases", tags=["releases"])
_EDIT_ENABLED = os.getenv("DMB_EDIT_ENABLED", "false").lower() == "true"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def build_edit_diff(source: dict, requested: dict) -> dict:
    def json_value(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    return {
        field: {"from": json_value(source[field]), "to": json_value(value)}
        for field, value in requested.items()
        if json_value(source.get(field)) != json_value(value)
    }


async def _delete_staged_keys(*keys: str | None) -> None:
    for key in keys:
        if not key:
            continue
        try:
            await storage.delete(key)
        except Exception:
            logger.exception("Failed to delete staged release object")


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
    artist_mappings: str | None = Form(None),
    edited_release_id: int | None = Form(None),
    submission_id: str | None = Form(None),
    requires_new_profile: bool | None = Form(None),
    is_edit: bool = Form(False),
    copyright_requested: bool = Form(False),
    explicit_content: bool | None = Form(None),
    policy_accepted: bool = Form(False),
    audio: UploadFile | None = File(None),
    cover: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    if is_edit and not _EDIT_ENABLED:
        raise HTTPException(status_code=503, detail="dmb_edit_disabled")
    if is_edit and audio is not None:
        raise HTTPException(status_code=400, detail="dmb_edit_audio_not_supported")
    try:
        validate_policy_acceptance(policy_accepted)
    except ReleaseValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    try:
        normalized_submission_id = normalize_submission_id(submission_id)
    except ReleaseValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

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
        if not source_release.dmb_release_id:
            raise HTTPException(status_code=409, detail="source_release_not_delivered")
        if not source_release.dmb_ean_upc or len(source_release.dmb_isrcs or []) != 1:
            raise HTTPException(status_code=409, detail="source_release_evidence_incomplete")

    final_explicit_content = (
        explicit_content
        if explicit_content is not None
        else source_release.explicit_content
        if source_release
        else False
    )

    if not is_edit and not all((song_name, release_date, genre, audio, cover)):
        raise HTTPException(status_code=400, detail="required_fields_missing")

    raw_song_name = song_name or (source_release.song_name if source_release else "")
    raw_genre = genre or (source_release.genre if source_release else "") or ""
    raw_sub_genre = (
        sub_genre
        if sub_genre is not None
        else source_release.sub_genre if source_release else None
    )
    if not raw_song_name or not raw_genre:
        raise HTTPException(status_code=400, detail="required_fields_missing")

    try:
        final_song_name = normalize_english_text(raw_song_name, "song_name")
        final_genre, final_sub_genre = validate_genre(raw_genre, raw_sub_genre)
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

    mappings_payload: str | list | None = artist_mappings
    if mappings_payload is None and source_release and source_release.artist_mappings:
        mappings_payload = source_release.artist_mappings
    try:
        final_artist_mappings = normalize_artist_mappings(
            mappings_payload,
            final_artists,
            legacy_requires_new_profile=(
                requires_new_profile
                if requires_new_profile is not None
                else source_release.requires_new_profile if source_release else False
            ),
            legacy_profile_email=(
                profile_email
                if profile_email is not None
                else source_release.profile_email if source_release else None
            ),
            legacy_mapping_spotify=(
                mapping_spotify
                if mapping_spotify is not None
                else source_release.mapping_spotify if source_release else None
            ),
            legacy_mapping_apple=(
                mapping_apple
                if mapping_apple is not None
                else source_release.mapping_apple if source_release else None
            ),
        )
    except ReleaseValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    first_primary = next(
        artist for artist in final_artists if artist["role"] == "primary"
    )
    legacy_mapping = next(
        mapping
        for mapping in final_artist_mappings
        if mapping["artist_name"].casefold() == first_primary["name"].casefold()
    )
    final_requires_new_profile = legacy_mapping["requires_new_profile"]
    final_profile_email = legacy_mapping["profile_email"]
    final_mapping_spotify = legacy_mapping["spotify_url"]
    final_mapping_apple = legacy_mapping["apple_music_url"]
    try:
        validate_notice_payload_size(
            song_name=final_song_name,
            artists=final_artists,
            producers=final_producer_names,
            legal_names=final_legal_names,
            genre=final_genre,
            sub_genre=final_sub_genre,
            artist_mappings=final_artist_mappings,
        )
    except ReleaseValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    audio_bytes_raw = await storage.read_audio(audio) if audio else None
    cover_bytes_raw = await storage.read_image(cover) if cover else None
    existing_audio_key = source_release.track_url if source_release and not audio else None
    existing_cover_key = source_release.cover_url if source_release and not cover else None
    if not audio_bytes_raw and not existing_audio_key:
        raise HTTPException(status_code=400, detail="audio_required")
    if not cover_bytes_raw and not existing_cover_key:
        raise HTTPException(status_code=400, detail="cover_required")

    total_cost = release_cost(is_edit, copyright_requested)
    preliminary_user_result = await db.execute(
        select(User).where(User.telegram_id == tg_id)
    )
    preliminary_user = preliminary_user_result.scalars().first()
    if not preliminary_user:
        raise HTTPException(status_code=404, detail="user_not_found")
    if not has_sufficient_credits(preliminary_user.credits, total_cost):
        raise HTTPException(status_code=400, detail="insufficient_credits")

    staged_audio_key = None
    staged_cover_key = None
    try:
        if audio_bytes_raw:
            audio_ext = os.path.splitext(audio.filename or "")[1].lower() or ".bin"
            staged_audio_key = await storage.upload(
                audio_bytes_raw,
                f"release-staging/{tg_id}/{normalized_submission_id}",
                f"source-audio{audio_ext}",
            )
        if cover_bytes_raw:
            cover_ext = os.path.splitext(cover.filename or "")[1].lower() or ".bin"
            staged_cover_key = await storage.upload(
                cover_bytes_raw,
                f"release-staging/{tg_id}/{normalized_submission_id}",
                f"source-cover{cover_ext}",
            )
    except Exception:
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        raise

    audio_key = staged_audio_key or existing_audio_key
    cover_key = staged_cover_key or existing_cover_key
    try:
        user_result = await db.execute(user_for_update_statement(tg_id))
    except Exception:
        await db.rollback()
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        raise
    user = user_result.scalars().first()
    if not user:
        await db.rollback()
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        raise HTTPException(status_code=404, detail="user_not_found")

    if normalized_submission_id:
        try:
            duplicate_result = await db.execute(
                select(Release).where(Release.submission_id == normalized_submission_id)
            )
        except Exception:
            await db.rollback()
            await _delete_staged_keys(staged_audio_key, staged_cover_key)
            raise
        duplicate = duplicate_result.scalars().first()
        if duplicate:
            await db.rollback()
            await _delete_staged_keys(staged_audio_key, staged_cover_key)
            if duplicate.user_id != tg_id:
                raise HTTPException(status_code=409, detail="submission_id_conflict")
            return {
                "status": "ok",
                "release_id": duplicate.id,
                "credits_left": user.credits,
                "cost_deducted": duplicate.charged_cost,
            }

    if not has_sufficient_credits(user.credits, total_cost):
        await db.rollback()
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        raise HTTPException(status_code=400, detail="insufficient_credits")

    edit_diff = {}
    if source_release:
        try:
            source_producers = json.loads(source_release.producers or "[]")
        except json.JSONDecodeError:
            source_producers = []
        edit_diff = build_edit_diff(
            {
                "song_name": source_release.song_name,
                "artists": source_release.artists,
                "producers": source_producers,
                "legal_names": source_release.legal_names,
                "release_date": source_release.release_date,
                "is_rerelease": source_release.is_rerelease,
                "original_release_date": source_release.original_release_date,
                "genre": source_release.genre,
                "sub_genre": source_release.sub_genre,
                "artist_mappings": source_release.artist_mappings,
                "explicit_content": source_release.explicit_content,
                "cover_replaced": False,
            },
            {
                "song_name": final_song_name,
                "artists": final_artists,
                "producers": final_producer_names,
                "legal_names": final_legal_names,
                "release_date": final_release_date,
                "is_rerelease": final_is_rerelease,
                "original_release_date": final_original_release_date,
                "genre": final_genre,
                "sub_genre": final_sub_genre,
                "artist_mappings": final_artist_mappings,
                "explicit_content": final_explicit_content,
                "cover_replaced": cover_bytes_raw is not None,
            },
        )

    release = Release(
        user_id=tg_id,
        track_url=audio_key,
        cover_url=cover_key,
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
        artist_mappings=final_artist_mappings,
        policy_accepted_at=_utc_now(),
        policy_version=os.getenv("POLICY_VERSION", "1.0").strip() or "1.0",
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        explicit_content=final_explicit_content,
        charged_cost=total_cost,
        submission_id=normalized_submission_id,
        source_release_id=source_release.id if source_release else None,
        source_dmb_release_id=source_release.dmb_release_id if source_release else None,
        edit_diff=edit_diff,
        status="staging",
    )
    user.credits -= total_cost
    db.add(release)
    try:
        await db.flush()
        add_ledger_entry(
            db,
            user_id=tg_id,
            amount=-total_cost,
            kind="release_charge",
            idempotency_key=f"release:{release.id}:charge",
            release_id=release.id,
            details={"song_name": release.song_name, "artist_name": release.artist_name},
        )
        db.add(
            ReleaseJob(
                release_id=release.id,
                phase="media",
                status="queued",
                source_audio_key=audio_key,
                source_cover_key=cover_key,
                convert_audio=audio_bytes_raw is not None,
                convert_cover=cover_bytes_raw is not None,
            )
        )
        await db.commit()
        await db.refresh(release)
    except IntegrityError:
        await db.rollback()
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        duplicate_result = await db.execute(
            select(Release).where(Release.submission_id == normalized_submission_id)
        )
        duplicate = duplicate_result.scalars().first()
        if duplicate and duplicate.user_id == tg_id:
            current_user_result = await db.execute(
                select(User).where(User.telegram_id == tg_id)
            )
            current_user = current_user_result.scalars().first()
            return {
                "status": "ok",
                "release_id": duplicate.id,
                "credits_left": current_user.credits if current_user else 0,
                "cost_deducted": duplicate.charged_cost,
            }
        raise HTTPException(status_code=409, detail="submission_id_conflict") from None
    except Exception:
        await db.rollback()
        await _delete_staged_keys(staged_audio_key, staged_cover_key)
        raise

    return {
        "status": "ok",
        "release_id": release.id,
        "credits_left": user.credits,
        "cost_deducted": total_cost,
    }
