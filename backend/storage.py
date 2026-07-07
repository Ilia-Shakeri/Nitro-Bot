import asyncio
import io
import os
import uuid

import boto3
from fastapi import HTTPException, UploadFile

from media_conversion import convert_audio_to_wav as _convert_audio_to_wav
from media_conversion import convert_cover_to_png

_S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
_S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "admin")
_S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "password123")
BUCKET_NAME = os.getenv("S3_BUCKET", "nitro-bot")

_client = boto3.client(
    "s3",
    endpoint_url=_S3_ENDPOINT,
    aws_access_key_id=_S3_ACCESS_KEY,
    aws_secret_access_key=_S3_SECRET_KEY,
    region_name="us-east-1",
)

_AUDIO_SIGS: list[tuple[bytes, bytes | None]] = [
    (b"\xff\xfb", None),
    (b"\xff\xf3", None),
    (b"\xff\xf2", None),
    (b"ID3", None),
    (b"RIFF", b"WAVE"),
]
_IMAGE_SIGS: list[tuple[bytes, bytes | None]] = [
    (b"\xff\xd8\xff", None),
    (b"\x89PNG\r\n\x1a\n", None),
    (b"RIFF", b"WEBP"),
]

_AUDIO_EXTENSIONS = {".mp3", ".wav"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _sig_match(header: bytes, sigs: list[tuple[bytes, bytes | None]]) -> bool:
    for prefix, riff_sub in sigs:
        if header.startswith(prefix):
            if riff_sub is None:
                return True
            if len(header) >= 12 and header[8:12] == riff_sub:
                return True
    return False


async def read_audio(file: UploadFile, max_mb: int = 50) -> bytes:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Music file must be MP3 or WAV")
    content = await file.read()
    if not _sig_match(content[:12], _AUDIO_SIGS):
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio file exceeds {max_mb} MB limit")
    return content


async def read_image(file: UploadFile, max_mb: int = 10) -> bytes:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Cover image must be JPG, PNG, or WEBP")
    content = await file.read()
    if not _sig_match(content[:12], _IMAGE_SIGS):
        raise HTTPException(status_code=400, detail="Invalid image file type")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image file exceeds {max_mb} MB limit")
    return content


async def convert_audio_to_wav(content: bytes) -> bytes:
    return await _convert_audio_to_wav(content)


async def process_cover(content: bytes) -> tuple[bytes, str]:
    return await convert_cover_to_png(content), "png"


async def upload(content: bytes, key_prefix: str, filename: str) -> str:
    key = f"{key_prefix}/{uuid.uuid4()}_{filename}"
    await asyncio.to_thread(_client.upload_fileobj, io.BytesIO(content), BUCKET_NAME, key)
    return key


async def presign(key: str, expires: int = 86400) -> str:
    return await asyncio.to_thread(
        _client.generate_presigned_url,
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=expires,
    )


async def download(key: str) -> bytes:
    def _download():
        obj = _client.get_object(Bucket=BUCKET_NAME, Key=key)
        return obj["Body"].read()
    return await asyncio.to_thread(_download)


async def ensure_bucket() -> None:
    try:
        await asyncio.to_thread(_client.create_bucket, Bucket=BUCKET_NAME)
    except Exception:
        pass
