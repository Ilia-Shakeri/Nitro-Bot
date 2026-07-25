from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ReleaseValidationError(ValueError):
    pass


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
        try:
            parsed = json.loads(raw or "[]")
        except (TypeError, json.JSONDecodeError):
            raise ReleaseValidationError(f"{field}_invalid") from None
    if not isinstance(parsed, list):
        raise ReleaseValidationError(f"{field}_invalid")
    return parsed


def normalize_names(raw: str | list[Any] | None, field: str) -> list[str]:
    parsed = _load_json_array(raw, field)
    names: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, str) or not item.strip():
            raise ReleaseValidationError(f"{field}_empty")
        name = item.strip()
        key = name.casefold()
        if key in seen:
            raise ReleaseValidationError(f"{field}_duplicate")
        seen.add(key)
        names.append(name)
    return names


def normalize_artists(raw: str | list[Any] | None) -> list[dict[str, str]]:
    parsed = _load_json_array(raw, "artists")
    if not parsed:
        raise ReleaseValidationError("artists_required")

    artists: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            raise ReleaseValidationError("artists_invalid")
        name_value = item.get("name")
        role_value = item.get("role")
        if not isinstance(name_value, str) or not name_value.strip():
            raise ReleaseValidationError("artists_empty")
        name = name_value.strip()
        key = name.casefold()
        if key in seen:
            raise ReleaseValidationError("artists_duplicate")
        seen.add(key)
        if role_value not in {"primary", "featured"}:
            raise ReleaseValidationError("artist_role_invalid")
        artists.append({"name": name, "role": role_value})

    if len(artists) == 1:
        artists[0]["role"] = "primary"
    if sum(artist["role"] == "primary" for artist in artists) != 1:
        raise ReleaseValidationError("artists_one_primary")
    return artists


def legacy_artist_name(artists: list[dict[str, str]]) -> str:
    primary = next(artist for artist in artists if artist["role"] == "primary")
    featured = [artist["name"] for artist in artists if artist["role"] == "featured"]
    return primary["name"] + (f" feat. {', '.join(featured)}" if featured else "")
