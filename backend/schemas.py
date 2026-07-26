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
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
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
    quote_asset: str | None = None
    quote_network: str | None = None
    quoted_amount: str | None = None
    quoted_usd_rate: str | None = None
    quote_created_at: datetime | None = None
    quote_expires_at: datetime | None = None
    stars_amount: int | None = None
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


class ArtistMappingOut(BaseModel):
    artist_name: str
    requires_new_profile: bool
    profile_email: str | None = None
    spotify_url: str | None = None
    apple_music_url: str | None = None


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
    artist_mappings: list[ArtistMappingOut] = Field(default_factory=list)
    policy_accepted_at: datetime | None = None
    policy_version: str | None = None
    status: str
    cover_url: str
    is_edit: bool
    copyright_requested: bool
    explicit_content: bool
    charged_cost: int
    refunded_at: datetime | None
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
    artist_mappings: list[ArtistMappingOut] = Field(default_factory=list)
    policy_accepted_at: datetime | None = None
    policy_version: str | None = None
    is_edit: bool
    copyright_requested: bool
    explicit_content: bool
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
    asset: str | None = None
    address: str | None = None
    number: str | None = None
    holder: str | None = None
    stars_per_nitro: int | None = None


class PaymentConfigOut(BaseModel):
    card: PaymentMethodOut | None = None
    usdt: PaymentMethodOut | None = None
    btc: PaymentMethodOut | None = None
    bnb: PaymentMethodOut | None = None
    usdt_bnb: PaymentMethodOut | None = None
    telegram_stars: PaymentMethodOut | None = None


class CryptoQuoteOut(BaseModel):
    transaction_id: int
    payment_method: str
    asset: str
    network: str
    amount: str
    usd_rate: str
    quoted_at: datetime
    expires_at: datetime


class StarsInvoiceOut(BaseModel):
    transaction_id: int
    invoice_url: str
    stars_amount: int


class OkResponse(BaseModel):
    status: str
