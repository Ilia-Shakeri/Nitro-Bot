import os

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Release
from schemas import PendingReleaseOut, OkResponse

_SECRET = os.getenv("SELENIUM_SECRET_KEY", "generate_a_secure_random_string_here")
_ALLOWED_STATUSES = {"pending", "processing", "completed", "failed"}

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_secret(authorization: str = Header(None)) -> None:
    if authorization != f"Bearer {_SECRET}":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/releases/pending", response_model=list[PendingReleaseOut])
async def get_pending_releases(
    _: None = Depends(_require_secret),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Release).where(Release.status == "pending"))
    return result.scalars().all()


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
