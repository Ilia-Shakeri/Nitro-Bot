import hmac
import os

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Release
from release_service import fail_release_and_refund
from schemas import PendingReleaseOut, OkResponse

_SECRET = os.getenv("SELENIUM_SECRET_KEY", "")
_ALLOWED_STATUSES = {"pending", "processing", "completed", "failed"}
_STATUS_TRANSITIONS = {
    "pending": {"processing"},
    "manual_staging": {"processing"},
    "processing": {"processing", "completed", "failed"},
    "completed": {"completed"},
    "failed": {"failed"},
}
_INSECURE_SECRETS = {"", "YOUR_SECURE_GENERATED_SELENIUM_TOKEN", "generate_a_secure_random_string_here"}

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_secret(authorization: str = Header(None)) -> None:
    # Reject calls if the secret is not configured or does not match.
    if _SECRET in _INSECURE_SECRETS:
        raise HTTPException(status_code=503, detail="Internal API secret not configured")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {_SECRET}"):
        raise HTTPException(status_code=403, detail="Forbidden")


def claimable_release_statement():
    return (
        select(Release)
        .where(Release.status.in_(("pending", "manual_staging")))
        .order_by(Release.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )


@router.get("/releases/pending", response_model=list[PendingReleaseOut])
async def get_pending_releases(
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(claimable_release_statement())
    releases = result.scalars().all()
    for release in releases:
        release.status = "processing"
    await db.commit()
    return releases


@router.post("/releases/{release_id}/status", response_model=OkResponse)
async def update_release_status(
    release_id: int,
    status: str = Form(...),
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    if status not in _ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed: {', '.join(sorted(_ALLOWED_STATUSES))}",
        )
    result = await db.execute(
        select(Release).where(Release.id == release_id).with_for_update()
    )
    release = result.scalars().first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if status not in _STATUS_TRANSITIONS.get(release.status, set()):
        await db.rollback()
        raise HTTPException(status_code=409, detail="release_status_transition_invalid")
    if status == "failed":
        await db.rollback()
        try:
            await fail_release_and_refund(
                db,
                release_id,
                "dmb_processing_failed",
                allowed_statuses={"processing", "failed"},
            )
        except ValueError:
            raise HTTPException(
                status_code=409, detail="release_status_transition_invalid"
            ) from None
        return {"status": "updated"}
    release.status = status
    await db.commit()
    return {"status": "updated"}
