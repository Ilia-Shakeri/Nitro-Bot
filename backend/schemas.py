from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Requests ──────────────────────────────────────────────────────────────────

class UserLanguageUpdate(BaseModel):
    language: str


# ── ORM-backed responses (from_attributes lets FastAPI serialize ORM objects) ──

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    telegram_id: int
    language_preference: str
    credits: int


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: int
    status: str
    payment_method: str
    created_at: datetime


class LedgerOut(BaseModel):
    id: str
    amount: int
    direction: str
    title: str
    status: str
    created_at: datetime


class SupportMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender: str
    message: str
    created_at: datetime


class SupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    status: str
    created_at: datetime
    messages: list[SupportMessageOut]


class ReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    song_name: str
    artist_name: str
    legal_name: str
    release_date: str
    genre: str | None
    mapping_spotify: str | None
    mapping_apple: str | None
    requires_new_profile: bool
    status: str
    cover_url: str
    is_edit: bool
    copyright_requested: bool
    created_at: datetime


class PendingReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    song_name: str
    artist_name: str
    legal_name: str
    release_date: str
    genre: str | None
    track_url: str
    cover_url: str
    mapping_spotify: str | None
    mapping_apple: str | None
    requires_new_profile: bool
    is_edit: bool
    copyright_requested: bool
    status: str
    created_at: datetime


# ── Plain responses ────────────────────────────────────────────────────────────

class ReleaseCreateResponse(BaseModel):
    status: str
    release_id: int
    credits_left: int
    cost_deducted: int


class ReceiptSubmitResponse(BaseModel):
    status: str
    transaction_id: int


class LanguageResponse(BaseModel):
    status: str
    language: str


class UsdtRateOut(BaseModel):
    # Live USDT price in Toman, used to compute the crypto amount for a top-up.
    rate_toman: int
    cached: bool


class OkResponse(BaseModel):
    status: str
