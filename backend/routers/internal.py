import hmac
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Literal

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Release
from release_service import fail_release_and_refund
from schemas import OkResponse, PendingReleaseOut

_SECRET = os.getenv("SELENIUM_SECRET_KEY", "")
_REVIEW_SECRET = os.getenv("DMB_REVIEW_SECRET_KEY", "")
_CREATE_ENABLED = os.getenv("DMB_CREATE_ENABLED", "false").lower() == "true"
_EDIT_ENABLED = os.getenv("DMB_EDIT_ENABLED", "false").lower() == "true"
_LEASE_SECONDS = max(120, int(os.getenv("DMB_LEASE_SECONDS", "900")))
_MAX_ATTEMPTS = max(1, int(os.getenv("DMB_MAX_ATTEMPTS", "3")))
_WORKER_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_DMB_ID_RE = re.compile(r"^(?=[A-Za-z0-9._:-]{1,128}$)(?=.*\d)[A-Za-z0-9._:-]+$")
_EAN_RE = re.compile(r"^\d{8,14}$")
_ISRC_RE = re.compile(r"^[A-Z0-9-]{8,20}$")
_ALLOWED_STATUSES = {"completed", "retry", "uncertain", "failed"}
_STATUS_TRANSITIONS = {
    "pending": {"processing"},
    "manual_staging": {"processing"},
    "processing": {"processing", "completed", "retry", "uncertain", "failed"},
    "dmb_verification_required": {"dmb_verification_required"},
    "completed": {"completed"},
    "failed": {"failed"},
}
_INSECURE_SECRETS = {
    "",
    "YOUR_SECURE_GENERATED_SELENIUM_TOKEN",
    "generate_a_secure_random_string_here",
    "generate_a_long_random_internal_token",
    "generate_a_different_long_review_token",
}

router = APIRouter(prefix="/internal", tags=["internal"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_secret(authorization: str = Header(None)) -> None:
    if _SECRET in _INSECURE_SECRETS:
        raise HTTPException(status_code=503, detail="Internal API secret not configured")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {_SECRET}"):
        raise HTTPException(status_code=403, detail="Forbidden")


def _require_review_secret(authorization: str = Header(None)) -> None:
    if _REVIEW_SECRET in _INSECURE_SECRETS:
        raise HTTPException(status_code=503, detail="DMB review secret not configured")
    if _SECRET and hmac.compare_digest(_REVIEW_SECRET, _SECRET):
        raise HTTPException(status_code=503, detail="DMB review secret must differ")
    if not authorization or not hmac.compare_digest(
        authorization, f"Bearer {_REVIEW_SECRET}"
    ):
        raise HTTPException(status_code=403, detail="Forbidden")


def _validated_worker_id(worker_id: str | None) -> str:
    if not worker_id or not _WORKER_ID_RE.fullmatch(worker_id):
        raise HTTPException(status_code=400, detail="dmb_worker_id_invalid")
    return worker_id


def _validated_reviewer_id(reviewer_id: str | None) -> str:
    if not reviewer_id or not _WORKER_ID_RE.fullmatch(reviewer_id):
        raise HTTPException(status_code=400, detail="dmb_reviewer_id_invalid")
    return reviewer_id


def _mode_enabled(mode: Literal["create", "edit"]) -> bool:
    return _EDIT_ENABLED if mode == "edit" else _CREATE_ENABLED


def claimable_release_statement(
    mode: Literal["create", "edit"] = "create",
    now: datetime | None = None,
):
    claim_time = now or utc_now()
    return (
        select(Release)
        .where(
            Release.is_edit.is_(mode == "edit"),
            Release.dmb_attempts < _MAX_ATTEMPTS,
            or_(
                Release.status.in_(("pending", "manual_staging")),
                and_(
                    Release.status == "processing",
                    or_(
                        Release.dmb_lease_expires_at.is_(None),
                        Release.dmb_lease_expires_at < claim_time,
                    ),
                ),
            ),
        )
        .order_by(Release.created_at.asc())
        .limit(1)
        .options(selectinload(Release.source_release))
        .with_for_update(skip_locked=True)
    )


def exhausted_release_statement(
    mode: Literal["create", "edit"],
    now: datetime,
):
    return (
        select(Release)
        .where(
            Release.is_edit.is_(mode == "edit"),
            Release.dmb_attempts >= _MAX_ATTEMPTS,
            or_(
                Release.status.in_(("pending", "manual_staging")),
                and_(
                    Release.status == "processing",
                    or_(
                        Release.dmb_lease_expires_at.is_(None),
                        Release.dmb_lease_expires_at < now,
                    ),
                ),
            ),
        )
        .order_by(Release.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )


def _parse_evidence(
    dmb_release_id: str | None,
    ean_upc: str | None,
    isrcs_json: str | None,
    evidence_path: str | None,
) -> tuple[str, str, list[str], str]:
    release_id = (dmb_release_id or "").strip()
    ean = (ean_upc or "").strip()
    evidence = (evidence_path or "").replace("\\", "/").strip()
    try:
        isrcs = json.loads(isrcs_json or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="dmb_evidence_invalid") from None
    path = PurePosixPath(evidence)
    if (
        not _DMB_ID_RE.fullmatch(release_id)
        or not _EAN_RE.fullmatch(ean)
        or not isinstance(isrcs, list)
        or not isrcs
        or len(isrcs) > 100
        or any(not isinstance(code, str) or not _ISRC_RE.fullmatch(code) for code in isrcs)
        or not evidence
        or len(evidence) > 512
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise HTTPException(status_code=400, detail="dmb_evidence_invalid")
    return release_id, ean, isrcs, evidence


def _submission_fingerprint(
    release_id: int,
    title: str,
    ean_upc: str,
    isrcs: list[str],
) -> str:
    value = json.dumps(
        {
            "release_id": release_id,
            "title": title,
            "ean_upc": ean_upc,
            "isrcs": isrcs,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_submit_checkpoint(
    release_id: int,
    title: str,
    ean_upc: str | None,
    isrcs_json: str | None,
    fingerprint: str | None,
) -> tuple[str, list[str], str] | None:
    if not any((ean_upc, isrcs_json, fingerprint)):
        return None
    ean = (ean_upc or "").strip()
    stored_fingerprint = (fingerprint or "").strip().lower()
    try:
        isrcs = json.loads(isrcs_json or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="dmb_checkpoint_invalid") from None
    if (
        not _EAN_RE.fullmatch(ean)
        or not isinstance(isrcs, list)
        or not isrcs
        or len(isrcs) > 100
        or any(not isinstance(code, str) or not _ISRC_RE.fullmatch(code) for code in isrcs)
        or not re.fullmatch(r"[a-f0-9]{64}", stored_fingerprint)
        or stored_fingerprint != _submission_fingerprint(release_id, title, ean, isrcs)
    ):
        raise HTTPException(status_code=400, detail="dmb_checkpoint_invalid")
    return ean, isrcs, stored_fingerprint


@router.get("/releases/pending", response_model=list[PendingReleaseOut])
async def get_pending_releases(
    mode: Literal["create", "edit"] = Query("create"),
    worker_id_header: str | None = Header(None, alias="X-DMB-Worker-ID"),
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    if not _mode_enabled(mode):
        raise HTTPException(status_code=503, detail=f"dmb_{mode}_disabled")
    worker_id = _validated_worker_id(worker_id_header)
    now = utc_now()

    exhausted_result = await db.execute(exhausted_release_statement(mode, now))
    exhausted = exhausted_result.scalars().first()
    if exhausted is not None:
        exhausted.dmb_last_error = "dmb_attempts_exhausted"
        exhausted.dmb_lease_owner = None
        exhausted.dmb_lease_expires_at = None
        await fail_release_and_refund(
            db,
            exhausted.id,
            "dmb_attempts_exhausted",
            allowed_statuses={"pending", "manual_staging", "processing", "failed"},
        )

    result = await db.execute(claimable_release_statement(mode, now))
    release = result.scalars().first()
    if release is None:
        await db.rollback()
        return []
    source_updates = {}
    if mode == "edit":
        source = release.source_release
        if source is None:
            await db.rollback()
            raise HTTPException(status_code=409, detail="edit_source_evidence_missing")
        source_updates = {
            "source_dmb_ean_upc": source.dmb_ean_upc,
            "source_dmb_isrcs": list(source.dmb_isrcs or []),
            "source_cover_url": source.cover_url,
        }
    release.status = "processing"
    release.dmb_attempts += 1
    release.dmb_lease_owner = worker_id
    release.dmb_lease_expires_at = now + timedelta(seconds=_LEASE_SECONDS)
    release.dmb_last_error = None
    payload = PendingReleaseOut.model_validate(release).model_copy(update=source_updates)
    await db.commit()
    return [payload]


@router.post("/releases/{release_id}/heartbeat", response_model=OkResponse)
async def heartbeat_release(
    release_id: int,
    worker_id_header: str | None = Header(None, alias="X-DMB-Worker-ID"),
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    worker_id = _validated_worker_id(worker_id_header)
    result = await db.execute(
        select(Release).where(Release.id == release_id).with_for_update()
    )
    release = result.scalars().first()
    if (
        release is None
        or release.status != "processing"
        or release.dmb_lease_owner != worker_id
    ):
        await db.rollback()
        raise HTTPException(status_code=409, detail="dmb_lease_lost")
    release.dmb_lease_expires_at = utc_now() + timedelta(seconds=_LEASE_SECONDS)
    await db.commit()
    return {"status": "leased"}


@router.post("/releases/{release_id}/status", response_model=OkResponse)
async def update_release_status(
    release_id: int,
    status: str = Form(...),
    dmb_release_id: str | None = Form(None),
    ean_upc: str | None = Form(None),
    isrcs_json: str | None = Form(None),
    evidence_path: str | None = Form(None),
    submission_fingerprint: str | None = Form(None),
    error: str | None = Form(None),
    worker_id_header: str | None = Header(None, alias="X-DMB-Worker-ID"),
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    if status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="dmb_status_invalid")
    worker_id = _validated_worker_id(worker_id_header)
    result = await db.execute(
        select(Release).where(Release.id == release_id).with_for_update()
    )
    release = result.scalars().first()
    if release is None:
        raise HTTPException(status_code=404, detail="Release not found")

    if release.status == "completed" and status == "completed":
        await db.rollback()
        return {"status": "updated"}
    if release.status != "processing" or release.dmb_lease_owner != worker_id:
        await db.rollback()
        raise HTTPException(status_code=409, detail="dmb_lease_lost")

    if status == "completed":
        stored_id, stored_ean, stored_isrcs, stored_evidence = _parse_evidence(
            dmb_release_id,
            ean_upc,
            isrcs_json,
            evidence_path,
        )
        completed_checkpoint = _parse_submit_checkpoint(
            release.id,
            release.song_name,
            stored_ean,
            json.dumps(stored_isrcs),
            submission_fingerprint,
        )
        if completed_checkpoint is None:
            await db.rollback()
            raise HTTPException(status_code=400, detail="dmb_checkpoint_invalid")
        release.dmb_release_id = stored_id
        release.dmb_ean_upc = stored_ean
        release.dmb_isrcs = stored_isrcs
        release.dmb_evidence_path = stored_evidence
        release.dmb_submission_fingerprint = completed_checkpoint[2]
        release.dmb_submission_started_at = release.dmb_submission_started_at or utc_now()
        release.dmb_submitted_at = utc_now()
        release.dmb_last_error = None
        release.status = "completed"
        release.dmb_lease_owner = None
        release.dmb_lease_expires_at = None
        await db.commit()
        return {"status": "updated"}

    reason = (error or "dmb_delivery_failed").strip()[:2000]
    if status == "uncertain":
        evidence = (evidence_path or f"results/{release_id}").replace("\\", "/")
        path = PurePosixPath(evidence)
        if len(evidence) > 512 or path.is_absolute() or ".." in path.parts:
            await db.rollback()
            raise HTTPException(status_code=400, detail="dmb_evidence_invalid")
        release.status = "dmb_verification_required"
        release.dmb_submission_started_at = utc_now()
        release.dmb_evidence_path = evidence
        checkpoint = _parse_submit_checkpoint(
            release.id,
            release.song_name,
            ean_upc,
            isrcs_json,
            submission_fingerprint,
        )
        if checkpoint is not None:
            release.dmb_ean_upc, release.dmb_isrcs, release.dmb_submission_fingerprint = checkpoint
        release.dmb_last_error = reason
        release.dmb_lease_owner = None
        release.dmb_lease_expires_at = None
        await db.commit()
        return {"status": "verification_required"}
    if status == "retry" and release.dmb_attempts < _MAX_ATTEMPTS:
        release.status = "manual_staging"
        release.dmb_last_error = reason
        release.dmb_lease_owner = None
        release.dmb_lease_expires_at = None
        await db.commit()
        return {"status": "retry"}

    release.dmb_last_error = reason
    release.dmb_lease_owner = None
    release.dmb_lease_expires_at = None
    await fail_release_and_refund(
        db,
        release_id,
        reason,
        allowed_statuses={"processing", "failed"},
    )
    return {"status": "failed"}


@router.post("/releases/{release_id}/verification", response_model=OkResponse)
async def resolve_release_verification(
    release_id: int,
    action: Literal["completed", "retry", "failed"] = Form(...),
    dmb_release_id: str | None = Form(None),
    ean_upc: str | None = Form(None),
    isrcs_json: str | None = Form(None),
    evidence_path: str | None = Form(None),
    reason: str | None = Form(None),
    reviewer_id_header: str | None = Header(None, alias="X-DMB-Reviewer-ID"),
    _: None = Depends(_require_review_secret),
    db: AsyncSession = Depends(get_db),
):
    reviewer_id = _validated_reviewer_id(reviewer_id_header)
    result = await db.execute(
        select(Release).where(Release.id == release_id).with_for_update()
    )
    release = result.scalars().first()
    if release is None:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Release not found")
    if release.status != "dmb_verification_required":
        await db.rollback()
        raise HTTPException(status_code=409, detail="dmb_verification_not_required")

    now = utc_now()
    release.dmb_reviewed_by = reviewer_id
    release.dmb_reviewed_at = now
    release.dmb_lease_owner = None
    release.dmb_lease_expires_at = None

    if action == "completed":
        stored_id, stored_ean, stored_isrcs, stored_evidence = _parse_evidence(
            dmb_release_id,
            ean_upc,
            isrcs_json,
            evidence_path,
        )
        if getattr(release, "dmb_submission_fingerprint", None) and (
            release.dmb_ean_upc != stored_ean
            or release.dmb_isrcs != stored_isrcs
            or release.dmb_submission_fingerprint
            != _submission_fingerprint(release.id, release.song_name, stored_ean, stored_isrcs)
        ):
            await db.rollback()
            raise HTTPException(status_code=409, detail="dmb_checkpoint_mismatch")
        release.dmb_release_id = stored_id
        release.dmb_ean_upc = stored_ean
        release.dmb_isrcs = stored_isrcs
        release.dmb_evidence_path = stored_evidence
        release.dmb_submitted_at = now
        release.dmb_last_error = None
        release.status = "completed"
        await db.commit()
        return {"status": "completed"}

    review_reason = (reason or "dmb_manual_review_failed").strip()[:2000]
    if action == "retry":
        if release.dmb_attempts >= _MAX_ATTEMPTS:
            await db.rollback()
            raise HTTPException(status_code=409, detail="dmb_attempts_exhausted")
        release.status = "manual_staging"
        release.dmb_last_error = f"manual_retry:{review_reason}"
        release.dmb_ean_upc = None
        release.dmb_isrcs = []
        release.dmb_submission_fingerprint = None
        release.dmb_submission_started_at = None
        release.dmb_evidence_path = None
        await db.commit()
        return {"status": "retry"}

    release.dmb_last_error = review_reason
    await fail_release_and_refund(
        db,
        release_id,
        review_reason,
        allowed_statuses={"dmb_verification_required", "failed"},
    )
    return {"status": "failed"}
