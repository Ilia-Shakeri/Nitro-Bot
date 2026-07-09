import asyncio
import io
import os
import subprocess
import tempfile
import uuid
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from fastapi import HTTPException, UploadFile
from PIL import Image

# Cover art is normalised to a square at least this many pixels per side so the
# DMB distribution platform always receives a high-resolution master.
MIN_COVER_PX = 3000

_S3_ENDPOINT   = os.getenv("S3_ENDPOINT",   "http://localhost:9000")
_S3_PUBLIC_ENDPOINT = os.getenv("S3_PUBLIC_ENDPOINT") or os.getenv("MINI_APP_URL") or _S3_ENDPOINT
_S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "admin")
_S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "password123")
BUCKET_NAME    = os.getenv("S3_BUCKET",     "nitro-bot")

_S3_CONFIG = Config(signature_version="s3v4", s3={"addressing_style": "path"})

_client = boto3.client(
    "s3",
    endpoint_url=_S3_ENDPOINT,
    aws_access_key_id=_S3_ACCESS_KEY,
    aws_secret_access_key=_S3_SECRET_KEY,
    region_name="us-east-1",
    config=_S3_CONFIG,
)

_presign_client = boto3.client(
    "s3",
    endpoint_url=_S3_PUBLIC_ENDPOINT,
    aws_access_key_id=_S3_ACCESS_KEY,
    aws_secret_access_key=_S3_SECRET_KEY,
    region_name="us-east-1",
    config=_S3_CONFIG,
)

if not urlparse(_S3_PUBLIC_ENDPOINT).scheme:
    raise RuntimeError("S3_PUBLIC_ENDPOINT must include http:// or https://")

_AUDIO_SIGS: list[tuple[bytes, bytes | None]] = [
    (b"\xff\xfb", None),
    (b"\xff\xf3", None),
    (b"\xff\xf2", None),
    (b"ID3",      None),
    (b"fLaC",     None),
    (b"RIFF",     b"WAVE"),
]
_IMAGE_SIGS: list[tuple[bytes, bytes | None]] = [
    (b"\xff\xd8\xff",       None),
    (b"\x89PNG\r\n\x1a\n", None),
    (b"RIFF",               b"WEBP"),
    (b"GIF87a",             None),
    (b"GIF89a",             None),
]


def _sig_match(header: bytes, sigs: list[tuple[bytes, bytes | None]]) -> bool:
    for prefix, riff_sub in sigs:
        if header.startswith(prefix):
            if riff_sub is None:
                return True
            if len(header) >= 12 and header[8:12] == riff_sub:
                return True
    return False


async def read_audio(file: UploadFile, max_mb: int = 50) -> bytes:
    content = await file.read()
    if not _sig_match(content[:12], _AUDIO_SIGS):
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio file exceeds {max_mb} MB limit")
    return content


async def read_image(file: UploadFile, max_mb: int = 10) -> bytes:
    content = await file.read()
    if not _sig_match(content[:12], _IMAGE_SIGS):
        raise HTTPException(status_code=400, detail="Invalid image file type")
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image file exceeds {max_mb} MB limit")
    return content


def _ffmpeg_to_wav(content: bytes) -> bytes:
    """Transcode arbitrary audio bytes to 16-bit/44.1kHz WAV.

    ffmpeg cannot write a valid WAV header to a non-seekable stdout pipe (it needs
    to seek back and patch the RIFF size fields), so we stage the data in temp files.
    """
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "input")
        dst = os.path.join(tmp, "output.wav")
        with open(src, "wb") as f:
            f.write(content)
        proc = subprocess.run(
            ["ffmpeg", "-y", "-i", src, "-acodec", "pcm_s16le", "-ar", "44100", dst],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise HTTPException(status_code=400, detail="Audio conversion failed")
        with open(dst, "rb") as f:
            return f.read()


async def convert_audio_to_wav(content: bytes) -> bytes:
    """Normalise any accepted audio (MP3/WAV/FLAC) to WAV for the DMB worker."""
    return await asyncio.to_thread(_ffmpeg_to_wav, content)


def _process_cover(content: bytes) -> tuple[bytes, str]:
    """Center-crop the cover to a square and ensure it is at least 3000x3000.

    Returns (bytes, extension). Images with transparency are emitted as PNG,
    everything else as JPEG to keep cover files small.
    """
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    )

    # Center-crop to a square — DSPs reject non-square cover art.
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Upscale toward the 3000px floor; never downscale a higher-res master.
    target = max(side, MIN_COVER_PX)
    if side != target:
        img = img.resize((target, target), Image.LANCZOS)

    out = io.BytesIO()
    if has_alpha:
        img.convert("RGBA").save(out, format="PNG", optimize=True)
        return out.getvalue(), "png"
    img.convert("RGB").save(out, format="JPEG", quality=95)
    return out.getvalue(), "jpg"


async def process_cover(content: bytes) -> tuple[bytes, str]:
    """Convert/upscale a user cover upload to a DSP-ready square master."""
    return await asyncio.to_thread(_process_cover, content)


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


async def ensure_bucket() -> None:
    try:
        await asyncio.to_thread(_client.create_bucket, Bucket=BUCKET_NAME)
    except Exception:
        pass
