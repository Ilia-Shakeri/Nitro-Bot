import asyncio
import io
import os
import subprocess
import tempfile

from fastapi import HTTPException
from PIL import Image

MIN_COVER_PX = 3000


def _ffmpeg_to_wav(content: bytes) -> bytes:
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


def _cover_to_png(content: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    target = max(side, MIN_COVER_PX)
    if side != target:
        img = img.resize((target, target), Image.LANCZOS)

    out = io.BytesIO()
    img.convert("RGBA").save(out, format="PNG", optimize=True)
    return out.getvalue()


async def convert_audio_to_wav(content: bytes) -> bytes:
    return await asyncio.to_thread(_ffmpeg_to_wav, content)


async def convert_cover_to_png(content: bytes) -> bytes:
    return await asyncio.to_thread(_cover_to_png, content)
