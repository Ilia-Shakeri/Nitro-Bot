from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        user = User(telegram_id=tg_id, language_preference="en", credits=0)
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
    audio: UploadFile = File(...),
    cover: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.credits < 10:
        raise HTTPException(status_code=400, detail="Not enough credits (10 required)")

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
        requires_new_profile=requires_new_profile
    )
    user.credits -= 10

    db.add(release)
    await db.commit()
    return {"status": "ok", "release_id": release.id, "credits_left": user.credits}

@app.post("/transactions/receipt")
async def submit_receipt(
    tg_id: int = Form(...),
    amount: int = Form(...),
    receipt: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receipt_key = f"receipts/{tg_id}/{uuid.uuid4()}_{receipt.filename}"
    
    # Prevent event loop blocking
    await asyncio.to_thread(s3_client.upload_fileobj, receipt.file, BUCKET_NAME, receipt_key)

    tx = Transaction(
        user_id=tg_id,
        amount=amount,
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
        ExpiresIn=86400 # URL valid for 24 hours
    )

    # Trigger admin notification
    await notify_admin_new_receipt(tx.id, amount, presigned_url)

    return {"status": "ok", "transaction_id": tx.id}