import asyncio
import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select, update

import storage
from database import AsyncSessionLocal
from models import Release, ReleaseJob, User
from release_service import fail_release_and_refund
from release_validation import normalize_names

logger = logging.getLogger("nitro.release_jobs")

LEASE_SECONDS = max(30, int(os.getenv("RELEASE_JOB_LEASE_SECONDS", "300")))
MAX_ATTEMPTS = max(1, int(os.getenv("RELEASE_JOB_MAX_ATTEMPTS", "5")))
POLL_SECONDS = max(1, int(os.getenv("RELEASE_JOB_POLL_SECONDS", "2")))
_WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def retry_delay_seconds(attempts: int) -> int:
    return min(300, 2 ** max(0, attempts - 1))


def claimable_job_statement(now: datetime):
    return (
        select(ReleaseJob)
        .where(
            or_(
                and_(
                    ReleaseJob.status.in_(("queued", "retry")),
                    ReleaseJob.next_attempt_at <= now,
                ),
                and_(
                    ReleaseJob.status == "processing",
                    ReleaseJob.lease_expires_at < now,
                ),
            )
        )
        .order_by(ReleaseJob.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )


async def _claim_one() -> int | None:
    now = utc_now()
    async with AsyncSessionLocal() as db:
        result = await db.execute(claimable_job_statement(now))
        job = result.scalars().first()
        if job is None:
            await db.rollback()
            return None
        job.status = "processing"
        job.attempts += 1
        job.lease_owner = _WORKER_ID
        job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        job.updated_at = now
        await db.commit()
        return job.id


async def _load_job(job_id: int) -> tuple[ReleaseJob, Release]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ReleaseJob, Release)
            .join(Release, Release.id == ReleaseJob.release_id)
            .where(ReleaseJob.id == job_id)
        )
        row = result.first()
        if row is None:
            raise RuntimeError("release_job_missing")
        job, release = row
        db.expunge(job)
        db.expunge(release)
        return job, release


def _assert_owned(job: ReleaseJob) -> None:
    if job.status != "processing" or job.lease_owner != _WORKER_ID:
        raise RuntimeError("release_job_lease_lost")


async def _heartbeat(job_id: int, stop: asyncio.Event) -> None:
    interval = max(10, LEASE_SECONDS // 3)
    while True:
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            return
        except TimeoutError:
            pass
        now = utc_now()
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(ReleaseJob)
                .where(
                    ReleaseJob.id == job_id,
                    ReleaseJob.status == "processing",
                    ReleaseJob.lease_owner == _WORKER_ID,
                )
                .values(
                    lease_expires_at=now + timedelta(seconds=LEASE_SECONDS),
                    updated_at=now,
                )
            )
            await db.commit()
            if result.rowcount != 1:
                raise RuntimeError("release_job_lease_lost")


async def _finish_media(job: ReleaseJob, release: Release) -> None:
    audio_key = job.source_audio_key
    cover_key = job.source_cover_key
    created_keys: list[str] = []
    try:
        audio_bytes = await storage.download(job.source_audio_key)
        cover_bytes = await storage.download(job.source_cover_key)
        if job.convert_audio:
            audio_bytes = await storage.convert_audio_to_wav(audio_bytes)
            audio_key = await storage.upload(
                audio_bytes, f"releases/{release.user_id}/{release.id}", "track.wav"
            )
            created_keys.append(audio_key)
        if job.convert_cover:
            cover_bytes, _ = await storage.process_cover(cover_bytes)
            cover_key = await storage.upload(
                cover_bytes, f"releases/{release.user_id}/{release.id}", "cover.png"
            )
            created_keys.append(cover_key)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ReleaseJob, Release)
                .join(Release, Release.id == ReleaseJob.release_id)
                .where(ReleaseJob.id == job.id)
                .with_for_update()
            )
            row = result.first()
            if row is None:
                raise RuntimeError("release_job_missing_after_media")
            stored_job, stored_release = row
            _assert_owned(stored_job)
            stored_release.track_url = audio_key
            stored_release.cover_url = cover_key
            stored_release.status = "notification_pending"
            stored_job.phase = "notify"
            stored_job.status = "queued"
            stored_job.attempts = 0
            stored_job.lease_owner = None
            stored_job.lease_expires_at = None
            stored_job.next_attempt_at = utc_now()
            stored_job.last_error = None
            stored_job.updated_at = utc_now()
            await db.commit()
    except Exception:
        for key in created_keys:
            try:
                await storage.delete(key)
            except Exception:
                logger.exception("Failed to clean partial release output")
        raise

    for source_key, converted in (
        (job.source_audio_key, job.convert_audio),
        (job.source_cover_key, job.convert_cover),
    ):
        if converted:
            try:
                await storage.delete(source_key)
            except Exception:
                logger.exception("Failed to clean staged release input")


async def _send_notice(job: ReleaseJob, release: Release, submitter: str) -> None:
    from bot import notify_admin_new_release

    audio_bytes, cover_bytes = await asyncio.gather(
        storage.download(release.track_url),
        storage.download(release.cover_url),
    )
    await notify_admin_new_release(
        submitter_tg_id=release.user_id,
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
        artist_mappings=release.artist_mappings,
        is_edit=release.is_edit,
        copyright_requested=release.copyright_requested,
        explicit_content=release.explicit_content,
        cost=release.charged_cost,
        submitter=submitter,
        audio_bytes=audio_bytes,
        audio_filename="track.wav",
        cover_bytes=cover_bytes,
        cover_filename="cover.png",
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ReleaseJob, Release)
            .join(Release, Release.id == ReleaseJob.release_id)
            .where(ReleaseJob.id == job.id)
            .with_for_update()
        )
        row = result.first()
        if row is None:
            raise RuntimeError("release_job_missing_after_notice")
        stored_job, stored_release = row
        _assert_owned(stored_job)
        stored_release.status = "manual_staging"
        stored_job.status = "completed"
        stored_job.lease_owner = None
        stored_job.lease_expires_at = None
        stored_job.last_error = None
        stored_job.updated_at = utc_now()
        await db.commit()


async def _record_failure(job_id: int, error: Exception) -> None:
    reason = f"{type(error).__name__}: {error}"[:2000]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ReleaseJob)
            .where(
                ReleaseJob.id == job_id,
                ReleaseJob.lease_owner == _WORKER_ID,
            )
            .with_for_update()
        )
        job = result.scalars().first()
        if job is None:
            await db.rollback()
            return
        job.last_error = reason
        job.lease_owner = None
        job.lease_expires_at = None
        job.updated_at = utc_now()
        if job.attempts >= MAX_ATTEMPTS:
            job.status = "dead"
            release_id = job.release_id
            await fail_release_and_refund(
                db,
                release_id,
                f"release_job_{job.phase}_failed",
                allowed_statuses={"staging", "notification_pending", "failed"},
            )
            return
        job.status = "retry"
        job.next_attempt_at = utc_now() + timedelta(
            seconds=retry_delay_seconds(job.attempts)
        )
        await db.commit()


async def process_one_job(job_id: int) -> None:
    heartbeat_stop = asyncio.Event()
    heartbeat_task = asyncio.create_task(_heartbeat(job_id, heartbeat_stop))
    try:
        job, release = await _load_job(job_id)
        if job.phase == "media":
            await _finish_media(job, release)
        elif job.phase == "notify":
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Release, User)
                    .join(User, User.telegram_id == Release.user_id)
                    .where(Release.id == release.id)
                )
                row = result.first()
                if row is None:
                    raise RuntimeError("release_missing_for_notice")
                release, user = row
                submitter = f"@{user.username}" if user.username else f"ID:{user.telegram_id}"
                db.expunge(release)
            await _send_notice(job, release, submitter)
        else:
            raise RuntimeError(f"release_job_phase_invalid:{job.phase}")
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("Release job %s failed", job_id)
        await _record_failure(job_id, exc)
    finally:
        heartbeat_stop.set()
        try:
            await heartbeat_task
        except Exception:
            logger.exception("Release job %s heartbeat stopped with error", job_id)


async def recover_legacy_staging() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Release)
            .outerjoin(ReleaseJob, ReleaseJob.release_id == Release.id)
            .where(Release.status == "staging", ReleaseJob.id.is_(None))
            .order_by(Release.id.asc())
        )
        releases = result.scalars().all()
        for release in releases:
            if release.track_url and release.cover_url:
                db.add(
                    ReleaseJob(
                        release_id=release.id,
                        phase="notify",
                        status="queued",
                        source_audio_key=release.track_url,
                        source_cover_key=release.cover_url,
                        convert_audio=False,
                        convert_cover=False,
                    )
                )
        await db.commit()

    for release in releases:
        if release.track_url and release.cover_url:
            continue
        async with AsyncSessionLocal() as refund_db:
            await fail_release_and_refund(
                refund_db,
                release.id,
                "legacy_staging_media_missing",
                allowed_statuses={"staging", "failed"},
            )


async def run_release_job_worker() -> None:
    await recover_legacy_staging()
    while True:
        try:
            job_id = await _claim_one()
            if job_id is None:
                await asyncio.sleep(POLL_SECONDS)
                continue
            await process_one_job(job_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Release job worker loop failed")
            await asyncio.sleep(POLL_SECONDS)
