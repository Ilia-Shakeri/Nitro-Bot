import asyncio
import io
import os
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from media_conversion import convert_audio_to_wav as _convert_audio_to_wav
from media_conversion import convert_cover_to_png

_ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
_S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
_S3_PUBLIC_ENDPOINT = os.getenv("S3_PUBLIC_ENDPOINT") or os.getenv("MINI_APP_URL") or _S3_ENDPOINT
_S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "local-development-access")
_S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "local-development-secret")
BUCKET_NAME = os.getenv("S3_BUCKET", "nitro-bot")

if _ENVIRONMENT == "production" and (
    not os.getenv("S3_ACCESS_KEY") or not os.getenv("S3_SECRET_KEY")
):
    raise RuntimeError("S3 credentials are required in production")

_client = boto3.client(
    "s3",
    endpoint_url=_S3_ENDPOINT,
    aws_access_key_id=_S3_ACCESS_KEY,
    aws_secret_access_key=_S3_SECRET_KEY,
    region_name="us-east-1",
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)
_presign_client = boto3.client(
    "s3",
    endpoint_url=_S3_PUBLIC_ENDPOINT,
    aws_access_key_id=_S3_ACCESS_KEY,
    aws_secret_access_key=_S3_SECRET_KEY,
    region_name="us-east-1",
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
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
        raise HTTPException(status_code=400, detail="audio_format_invalid")
    content = await file.read()
    if not _sig_match(content[:12], _AUDIO_SIGS):
        raise HTTPException(status_code=400, detail="audio_type_invalid")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="audio_too_large")
    return content


async def read_image(file: UploadFile, max_mb: int = 10) -> bytes:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="image_format_invalid")
    content = await file.read()
    if not _sig_match(content[:12], _IMAGE_SIGS):
        raise HTTPException(status_code=400, detail="image_type_invalid")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="image_too_large")
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
        _presign_client.generate_presigned_url,
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=expires,
    )


async def download(key: str) -> bytes:
    def _download():
        obj = _client.get_object(Bucket=BUCKET_NAME, Key=key)
        return obj["Body"].read()
    return await asyncio.to_thread(_download)


async def delete(key: str) -> None:
    if not key:
        return
    await asyncio.to_thread(_client.delete_object, Bucket=BUCKET_NAME, Key=key)


async def ensure_bucket() -> None:
    try:
        await asyncio.to_thread(_client.create_bucket, Bucket=BUCKET_NAME)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in {"BucketAlreadyExists", "BucketAlreadyOwnedByYou"}:
            raise
