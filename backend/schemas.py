from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class UserLanguageUpdate(BaseModel):
    language: str


# ── ORM-backed responses (from_attributes lets FastAPI serialize ORM objects) ──

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    telegram_id: int
    language_preference: str
    credits: int
    referral_points: int = 0


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: int
    status: str
    payment_method: str
    usd_amount_cents: int
    toman_amount_cents: int | None
    created_at: datetime


class LedgerOut(BaseModel):
    id: str
    amount: int
    direction: str
    title: str
    title_key: str
    title_params: dict[str, str | int] = Field(default_factory=dict)
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


class ReleaseArtistOut(BaseModel):
    name: str
    role: Literal["primary", "featured"]


class ReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    song_name: str
    artist_name: str
    artists: list[ReleaseArtistOut]
    producers: str | None
    legal_name: str
    legal_names: list[str]
    release_date: date
    is_rerelease: bool
    original_release_date: date | None
    genre: str | None
    sub_genre: str | None
    mapping_spotify: str | None
    mapping_apple: str | None
    profile_email: str | None
    requires_new_profile: bool
    status: str
    cover_url: str
    is_edit: bool
    copyright_requested: bool
    charged_cost: int
    created_at: datetime


class PendingReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    song_name: str
    artist_name: str
    artists: list[ReleaseArtistOut]
    producers: str | None
    legal_name: str
    legal_names: list[str]
    release_date: date
    is_rerelease: bool
    original_release_date: date | None
    genre: str | None
    sub_genre: str | None
    track_url: str
    cover_url: str
    mapping_spotify: str | None
    mapping_apple: str | None
    profile_email: str | None
    requires_new_profile: bool
    is_edit: bool
    copyright_requested: bool
    charged_cost: int
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


class PricingOut(BaseModel):
    nitro_usd_price_cents: int
    original_release_price: int
    discounted_release_price: int
    copyright_price: int
    edit_release_price: int
    minimum_topup_nitro: int


class PaymentMethodOut(BaseModel):
    network: str | None = None
    address: str | None = None
    number: str | None = None
    holder: str | None = None


class PaymentConfigOut(BaseModel):
    card: PaymentMethodOut | None = None
    btc: PaymentMethodOut | None = None
    usdt: PaymentMethodOut | None = None


class OkResponse(BaseModel):
    status: str
