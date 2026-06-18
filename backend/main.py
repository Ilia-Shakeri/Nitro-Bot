from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import os
from pydantic import BaseModel
import uuid
import boto3
import asyncio
from contextlib import asynccontextmanager

from models import Base, User, Transaction, Release
from bot import dp, bot, notify_admin_new_receipt

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/nitrodb")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://nitrobot.duckdns.org")
SELENIUM_SECRET_KEY = os.getenv("SELENIUM_SECRET_KEY", "generate_a_secure_random_string_here")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY", "admin"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY", "password123"),
    region_name="us-east-1"
)
BUCKET_NAME = "nitro-bot"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize S3 Bucket on startup
    try:
        await asyncio.to_thread(s3_client.create_bucket, Bucket=BUCKET_NAME)
    except Exception:
        pass 
    
    # Start Telegram bot polling
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    
    # Graceful shutdown
    polling_task.cancel()
    await bot.session.close()

app = FastAPI(title="Nitro Bot API", lifespan=lifespan)

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[MINI_APP_URL, "http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserLanguageUpdate(BaseModel):
    language: str

@app.get("/users/{tg_id}")
async def get_user(tg_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=tg_id, language_preference="fa", credits=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return {"telegram_id": user.telegram_id, "language_preference": user.language_preference, "credits": user.credits}

@app.post("/users/{tg_id}/language")
async def update_language(tg_id: int, update: UserLanguageUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.language_preference = update.language
    await db.commit()
    return {"status": "ok", "language": user.language_preference}

@app.post("/releases")
async def create_release(
    tg_id: int = Form(...),
    song_name: str = Form(...),
    artist_name: str = Form(...),
    legal_name: str = Form(...),
    release_date: str = Form(...),
    mapping_spotify: str = Form(None),
    mapping_apple: str = Form(None),
    requires_new_profile: bool = Form(False),
    is_edit: bool = Form(False),
    copyright_requested: bool = Form(False),
    audio: UploadFile = File(...),
    cover: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Dynamic Pricing Engine
    base_cost = 1 if is_edit else 10
    total_cost = base_cost + (2 if copyright_requested else 0)

    if user.credits < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough credits ({total_cost} required)")

    audio_key = f"releases/{tg_id}/{uuid.uuid4()}_{audio.filename}"
    cover_key = f"releases/{tg_id}/{uuid.uuid4()}_{cover.filename}"

    # Prevent event loop blocking during file upload
    await asyncio.to_thread(s3_client.upload_fileobj, audio.file, BUCKET_NAME, audio_key)
    await asyncio.to_thread(s3_client.upload_fileobj, cover.file, BUCKET_NAME, cover_key)

    release = Release(
        user_id=tg_id,
        track_url=audio_key,
        cover_url=cover_key,
        song_name=song_name,
        artist_name=artist_name,
        legal_name=legal_name,
        release_date=release_date,
        mapping_spotify=mapping_spotify,
        mapping_apple=mapping_apple,
        requires_new_profile=requires_new_profile,
        is_edit=is_edit,
        copyright_requested=copyright_requested,
        status="pending"
    )
    
    user.credits -= total_cost

    db.add(release)
    await db.commit()
    return {"status": "ok", "release_id": release.id, "credits_left": user.credits, "cost_deducted": total_cost}

@app.post("/transactions/receipt")
async def submit_receipt(
    tg_id: int = Form(...),
    amount: int = Form(...),
    payment_method: str = Form(...),
    receipt: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receipt_key = f"receipts/{tg_id}/{uuid.uuid4()}_{receipt.filename}"
    
    await asyncio.to_thread(s3_client.upload_fileobj, receipt.file, BUCKET_NAME, receipt_key)

    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        payment_method=payment_method,
        status="pending",
        receipt_url=receipt_key
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    # Generate a pre-signed URL for admins to securely view the receipt
    presigned_url = await asyncio.to_thread(
        s3_client.generate_presigned_url,
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': receipt_key},
        ExpiresIn=86400 
    )

    await notify_admin_new_receipt(tx.id, amount, payment_method, presigned_url)
    return {"status": "ok", "transaction_id": tx.id}

# ==========================================
# Internal Worker Endpoints (For Selenium)
# ==========================================
@app.get("/internal/releases/pending")
async def get_pending_releases(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if authorization != f"Bearer {SELENIUM_SECRET_KEY}":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    result = await db.execute(select(Release).where(Release.status == "pending"))
    releases = result.scalars().all()
    return releases

@app.post("/internal/releases/{release_id}/status")
async def update_release_status(release_id: int, status: str = Form(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if authorization != f"Bearer {SELENIUM_SECRET_KEY}":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    result = await db.execute(select(Release).where(Release.id == release_id))
    release = result.scalars().first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
        
    release.status = status
    await db.commit()
    return {"status": "updated"}