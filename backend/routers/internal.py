import hmac
import os

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Release
from schemas import PendingReleaseOut, OkResponse
import storage

_SECRET = os.getenv("SELENIUM_SECRET_KEY", "")
_ALLOWED_STATUSES = {"pending", "processing", "completed", "failed"}
_INSECURE_SECRETS = {"", "YOUR_SECURE_GENERATED_SELENIUM_TOKEN", "generate_a_secure_random_string_here"}

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_secret(authorization: str = Header(None)) -> None:
    # Reject calls if the secret is not configured or does not match.
    if _SECRET in _INSECURE_SECRETS:
        raise HTTPException(status_code=503, detail="Internal API secret not configured")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {_SECRET}"):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/releases/pending", response_model=list[PendingReleaseOut])
async def get_pending_releases(
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Release).where(Release.status == "pending"))
    releases = result.scalars().all()
    import asyncio
    async def presign_urls(release):
        if release.cover_url:
            release.cover_url = await storage.presign(release.cover_url)
        if release.track_url:
            release.track_url = await storage.presign(release.track_url)
    await asyncio.gather(*[presign_urls(r) for r in releases])
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
    result = await db.execute(select(Release).where(Release.id == release_id))
    release = result.scalars().first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    release.status = status
    await db.commit()
    return {"status": "updated"}
