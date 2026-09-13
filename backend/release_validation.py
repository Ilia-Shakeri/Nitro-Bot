from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from release_genres import GENRE_TREE


class ReleaseValidationError(ValueError):
    pass


_ENGLISH_TEXT_RE = re.compile(r"^[A-Za-z0-9 .,'&()\[\]\-_/+!?:#]+$")
_ENGLISH_ALNUM_RE = re.compile(r"[A-Za-z0-9]")
_ASCII_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
_SUBMISSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_MAX_TEXT_LENGTH = 200
_MAX_NAMES = 20
_MAX_JSON_LENGTH = 32_768
_MAX_URL_LENGTH = 2_048
_MAX_NOTICE_DYNAMIC_LENGTH = 3_000


def normalize_english_text(value: Any, field: str = "text") -> str:
    if not isinstance(value, str):
        raise ReleaseValidationError("english_only_input")
    normalized = " ".join(value.strip().split())
    if (
        not normalized
        or not _ENGLISH_TEXT_RE.fullmatch(normalized)
        or not _ENGLISH_ALNUM_RE.search(normalized)
    ):
        raise ReleaseValidationError("english_only_input")
    if len(normalized) > _MAX_TEXT_LENGTH:
        raise ReleaseValidationError(f"{field}_too_long")
    return normalized


def normalize_submission_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ReleaseValidationError("submission_id_invalid")
    normalized = value.strip()
    if not _SUBMISSION_ID_RE.fullmatch(normalized):
        raise ReleaseValidationError("submission_id_invalid")
    return normalized


def validate_genre(genre: Any, sub_genre: Any) -> tuple[str, str | None]:
    if not isinstance(genre, str):
        raise ReleaseValidationError("genre_invalid")
    normalized_genre = genre.strip()
    allowed_sub_genres = GENRE_TREE.get(normalized_genre)
    if allowed_sub_genres is None:
        raise ReleaseValidationError("genre_invalid")
    if sub_genre in (None, ""):
        return normalized_genre, None
    if not isinstance(sub_genre, str):
        raise ReleaseValidationError("sub_genre_invalid")
    normalized_sub_genre = sub_genre.strip()
    if normalized_sub_genre not in allowed_sub_genres:
        raise ReleaseValidationError("sub_genre_invalid")
    return normalized_genre, normalized_sub_genre


def validate_notice_payload_size(
    *,
    song_name: str,
    artists: list[dict[str, str]],
    producers: list[str],
    legal_names: list[str],
    genre: str,
    sub_genre: str | None,
    artist_mappings: list[dict[str, Any]],
) -> None:
    values: list[str] = [song_name, genre, sub_genre or ""]
    values.extend(artist["name"] for artist in artists)
    values.extend(producers)
    values.extend(legal_names)
    for mapping in artist_mappings:
        values.extend(
            str(mapping.get(field) or "")
            for field in (
                "artist_name",
                "profile_email",
                "spotify_url",
                "apple_music_url",
            )
        )
    if sum(map(len, values)) > _MAX_NOTICE_DYNAMIC_LENGTH:
        raise ReleaseValidationError("release_metadata_too_large")


def validate_policy_acceptance(value: bool | None) -> None:
    if value is not True:
        raise ReleaseValidationError("policy_acceptance_required")


def current_calendar_date() -> date:
    timezone_name = os.getenv("APP_TIMEZONE", "UTC")
    try:
        return (
            date.today()
            if timezone_name == "local"
            else datetime.now(ZoneInfo(timezone_name)).date()
        )
    except ZoneInfoNotFoundError:
        raise RuntimeError("APP_TIMEZONE is invalid") from None


def parse_iso_date(value: str | date | None, field: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat((value or "").strip())
    except (TypeError, ValueError):
        raise ReleaseValidationError(f"{field}_invalid") from None


def validate_release_dates(
    *,
    release_date: str | date | None,
    is_rerelease: bool,
    original_release_date: str | date | None,
    today: date | None = None,
    allow_unchanged_historical: bool = False,
) -> tuple[date, date | None]:
    current_date = today or current_calendar_date()
    scheduled = parse_iso_date(release_date, "release_date")
    if scheduled < current_date and not allow_unchanged_historical:
        raise ReleaseValidationError(
            "rerelease_date_past" if is_rerelease else "release_date_past"
        )

    if not is_rerelease:
        return scheduled, None

    if original_release_date in (None, ""):
        raise ReleaseValidationError("original_release_date_required")
    original = parse_iso_date(original_release_date, "original_release_date")
    if original >= scheduled:
        raise ReleaseValidationError("original_release_date_not_before_rerelease")
    return scheduled, original


def _load_json_array(raw: str | list[Any] | None, field: str) -> list[Any]:
    if isinstance(raw, list):
        parsed = raw
    else:
        if isinstance(raw, str) and len(raw) > _MAX_JSON_LENGTH:
            raise ReleaseValidationError(f"{field}_too_large")
        try:
            parsed = json.loads(raw or "[]")
        except (TypeError, json.JSONDecodeError):
            raise ReleaseValidationError(f"{field}_invalid") from None
    if not isinstance(parsed, list):
        raise ReleaseValidationError(f"{field}_invalid")
    return parsed


def normalize_names(raw: str | list[Any] | None, field: str) -> list[str]:
    parsed = _load_json_array(raw, field)
    if len(parsed) > _MAX_NAMES:
        raise ReleaseValidationError(f"{field}_max")
    names: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, str) or not item.strip():
            raise ReleaseValidationError(f"{field}_empty")
        name = normalize_english_text(item, field)
        key = name.casefold()
        if key in seen:
            raise ReleaseValidationError(f"{field}_duplicate")
        seen.add(key)
        names.append(name)
    return names


def normalize_required_names(raw: str | list[Any] | None, field: str) -> list[str]:
    names = normalize_names(raw, field)
    if not names:
        raise ReleaseValidationError(f"{field}_required")
    return names


def normalize_artists(raw: str | list[Any] | None) -> list[dict[str, str]]:
    parsed = _load_json_array(raw, "artists")
    if not parsed:
        raise ReleaseValidationError("artists_required")
    if len(parsed) > 6:
        raise ReleaseValidationError("artists_max")

    artists: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            raise ReleaseValidationError("artists_invalid")
        name_value = item.get("name")
        role_value = item.get("role")
        if not isinstance(name_value, str) or not name_value.strip():
            raise ReleaseValidationError("artists_empty")
        name = normalize_english_text(name_value, "artists")
        key = name.casefold()
        if key in seen:
            raise ReleaseValidationError("artists_duplicate")
        seen.add(key)
        if role_value not in {"primary", "featured"}:
            raise ReleaseValidationError("artist_role_invalid")
        artists.append({"name": name, "role": role_value})

    if len(artists) == 1:
        artists[0]["role"] = "primary"
    primary_count = sum(artist["role"] == "primary" for artist in artists)
    if primary_count == 0:
        raise ReleaseValidationError("artists_primary_required")
    if primary_count > 3:
        raise ReleaseValidationError("artists_primary_max")
    return artists


def legacy_artist_name(artists: list[dict[str, str]]) -> str:
    primary = [artist["name"] for artist in artists if artist["role"] == "primary"]
    featured = [artist["name"] for artist in artists if artist["role"] == "featured"]
    return ", ".join(primary) + (f" feat. {', '.join(featured)}" if featured else "")


def _normalize_artist_url(value: Any, platform: str) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ReleaseValidationError("artist_mapping_url_invalid")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > _MAX_URL_LENGTH:
        raise ReleaseValidationError("artist_mapping_url_invalid")
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError:
        raise ReleaseValidationError("artist_mapping_url_invalid") from None
    parsed = urlparse(normalized)
    try:
        port = parsed.port
    except ValueError:
        raise ReleaseValidationError("artist_mapping_url_invalid") from None
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise ReleaseValidationError("artist_mapping_url_invalid")
    host = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]
    if platform == "spotify":
        valid_path = len(path_parts) == 2 and path_parts[0] == "artist" and bool(path_parts[1])
        if host != "open.spotify.com" or not valid_path:
            raise ReleaseValidationError("artist_mapping_url_invalid")
    elif platform == "apple":
        artist_index = 0 if path_parts[:1] == ["artist"] else 1
        valid_path = (
            len(path_parts) >= artist_index + 3
            and path_parts[artist_index] == "artist"
            and path_parts[-1].isdigit()
        )
        if host != "music.apple.com" or not valid_path:
            raise ReleaseValidationError("artist_mapping_url_invalid")
    else:
        raise RuntimeError("artist_mapping_platform_invalid")
    return normalized


def _normalize_ascii_email(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ReleaseValidationError("artist_mapping_email_invalid")
    normalized = value.strip()
    if not normalized:
        return None
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError:
        raise ReleaseValidationError("artist_mapping_email_invalid") from None
    if len(normalized) > 254 or not _ASCII_EMAIL_RE.fullmatch(normalized):
        raise ReleaseValidationError("artist_mapping_email_invalid")
    return normalized


def normalize_artist_mappings(
    raw: str | list[Any] | None,
    artists: list[dict[str, str]],
    *,
    legacy_requires_new_profile: bool | None = None,
    legacy_profile_email: str | None = None,
    legacy_mapping_spotify: str | None = None,
    legacy_mapping_apple: str | None = None,
) -> list[dict[str, Any]]:
    parsed = _load_json_array(raw, "artist_mappings")
    if not parsed and len(artists) == 1:
        parsed = [
            {
                "artist_name": artists[0]["name"],
                "requires_new_profile": bool(legacy_requires_new_profile),
                "profile_email": legacy_profile_email,
                "spotify_url": legacy_mapping_spotify,
                "apple_music_url": legacy_mapping_apple,
            }
        ]
    if len(parsed) != len(artists):
        raise ReleaseValidationError("artist_mappings_incomplete")

    canonical_names = {artist["name"].casefold(): artist["name"] for artist in artists}
    seen: set[str] = set()
    mappings: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for item in parsed:
        if not isinstance(item, dict):
            raise ReleaseValidationError("artist_mappings_invalid")
        raw_name = item.get("artist_name")
        if not isinstance(raw_name, str):
            raise ReleaseValidationError("artist_mapping_unknown_artist")
        key = " ".join(raw_name.strip().split()).casefold()
        canonical_name = canonical_names.get(key)
        if canonical_name is None:
            raise ReleaseValidationError("artist_mapping_unknown_artist")
        if key in seen:
            raise ReleaseValidationError("artist_mapping_duplicate")
        seen.add(key)

        requires_new_profile = item.get("requires_new_profile")
        if not isinstance(requires_new_profile, bool):
            raise ReleaseValidationError("artist_mappings_invalid")
        email = _normalize_ascii_email(item.get("profile_email"))
        spotify = _normalize_artist_url(item.get("spotify_url"), "spotify")
        apple = _normalize_artist_url(item.get("apple_music_url"), "apple")
        if requires_new_profile:
            if not email:
                raise ReleaseValidationError("artist_mapping_email_required")
            spotify = None
            apple = None
        else:
            if not spotify and not apple:
                raise ReleaseValidationError("artist_mapping_link_required")
            email = None
        by_name[key] = {
            "artist_name": canonical_name,
            "requires_new_profile": requires_new_profile,
            "profile_email": email,
            "spotify_url": spotify,
            "apple_music_url": apple,
        }

    for artist in artists:
        mapping = by_name.get(artist["name"].casefold())
        if mapping is None:
            raise ReleaseValidationError("artist_mappings_incomplete")
        mappings.append(mapping)
    return mappings


def validate_release_mapping(
    *,
    requires_new_profile: bool,
    profile_email: str | None,
    mapping_spotify: str | None,
    mapping_apple: str | None,
) -> tuple[str | None, str | None, str | None]:
    email = _normalize_ascii_email(profile_email)
    spotify = _normalize_artist_url(mapping_spotify, "spotify")
    apple = _normalize_artist_url(mapping_apple, "apple")
    if requires_new_profile:
        if not email:
            raise ReleaseValidationError("profile_email_required")
        spotify = None
        apple = None
    elif not spotify and not apple:
        raise ReleaseValidationError("mapping_required")
    else:
        email = None
    return email, spotify, apple
