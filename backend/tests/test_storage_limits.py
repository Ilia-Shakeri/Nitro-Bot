import pytest
from fastapi import HTTPException

import storage


class ChunkedUpload:
    def __init__(self, data: bytes, filename: str):
        self.data = data
        self.filename = filename
        self.offset = 0
        self.read_sizes: list[int] = []

    async def read(self, size: int) -> bytes:
        self.read_sizes.append(size)
        chunk = self.data[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


@pytest.mark.asyncio
async def test_audio_is_read_in_bounded_chunks():
    upload = ChunkedUpload(b"RIFFxxxxWAVE" + b"a" * 32, "track.wav")
    content = await storage.read_audio(upload, max_mb=1)
    assert content == upload.data
    assert upload.read_sizes
    assert max(upload.read_sizes) <= storage._READ_CHUNK_BYTES


@pytest.mark.asyncio
async def test_audio_stops_after_hard_byte_limit():
    upload = ChunkedUpload(
        b"RIFFxxxxWAVE" + b"a" * (1024 * 1024),
        "track.wav",
    )
    with pytest.raises(HTTPException) as exc:
        await storage.read_audio(upload, max_mb=1)
    assert exc.value.detail == "audio_too_large"
    assert upload.offset == 1024 * 1024 + 1
