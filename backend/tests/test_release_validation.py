from datetime import date

import pytest

from release_validation import (
    ReleaseValidationError,
    normalize_artists,
    normalize_names,
    normalize_required_names,
    validate_release_dates,
)

TODAY = date(2026, 7, 26)


def test_past_scheduled_date_rejected():
    with pytest.raises(ReleaseValidationError, match="release_date_past"):
        validate_release_dates(
            release_date="2026-07-25",
            is_rerelease=False,
            original_release_date=None,
            today=TODAY,
        )


@pytest.mark.parametrize("value", ["2026-07-26", "2026-08-01"])
def test_today_and_future_scheduled_dates_are_accepted(value):
    scheduled, original = validate_release_dates(
        release_date=value,
        is_rerelease=False,
        original_release_date=None,
        today=TODAY,
    )
    assert scheduled == date.fromisoformat(value)
    assert original is None


def test_unchanged_historical_edit_date_is_accepted():
    scheduled, _ = validate_release_dates(
        release_date="2020-01-01",
        is_rerelease=False,
        original_release_date=None,
        today=TODAY,
        allow_unchanged_historical=True,
    )
    assert scheduled == date(2020, 1, 1)


def test_rerelease_requires_original_date():
    with pytest.raises(ReleaseValidationError, match="original_release_date_required"):
        validate_release_dates(
            release_date="2026-07-26",
            is_rerelease=True,
            original_release_date=None,
            today=TODAY,
        )


def test_rerelease_date_cannot_be_past():
    with pytest.raises(ReleaseValidationError, match="rerelease_date_past"):
        validate_release_dates(
            release_date="2026-07-25",
            is_rerelease=True,
            original_release_date="2020-01-01",
            today=TODAY,
        )


def test_original_date_may_be_historical_and_must_be_before_rerelease():
    scheduled, original = validate_release_dates(
        release_date="2026-07-26",
        is_rerelease=True,
        original_release_date="1999-12-31",
        today=TODAY,
    )
    assert original == date(1999, 12, 31)
    assert original < scheduled

    with pytest.raises(
        ReleaseValidationError,
        match="original_release_date_not_before_rerelease",
    ):
        validate_release_dates(
            release_date="2026-07-26",
            is_rerelease=True,
            original_release_date="2026-07-26",
            today=TODAY,
        )


def test_single_artist_is_automatically_primary():
    artists = normalize_artists([{"name": "  One  ", "role": "featured"}])
    assert artists == [{"name": "One", "role": "primary"}]


def test_artist_list_requires_exactly_one_primary():
    with pytest.raises(ReleaseValidationError, match="artists_one_primary"):
        normalize_artists(
            [
                {"name": "One", "role": "featured"},
                {"name": "Two", "role": "featured"},
            ]
        )
    with pytest.raises(ReleaseValidationError, match="artists_one_primary"):
        normalize_artists(
            [
                {"name": "One", "role": "primary"},
                {"name": "Two", "role": "primary"},
            ]
        )


def test_duplicate_artists_are_case_insensitive():
    with pytest.raises(ReleaseValidationError, match="artists_duplicate"):
        normalize_artists(
            [
                {"name": "Artist", "role": "primary"},
                {"name": " artist ", "role": "featured"},
            ]
        )


def test_duplicate_legal_names_are_case_insensitive():
    with pytest.raises(ReleaseValidationError, match="legal_names_duplicate"):
        normalize_names('["Name", " name "]', "legal_names")


def test_malformed_json_is_rejected():
    with pytest.raises(ReleaseValidationError, match="artists_invalid"):
        normalize_artists("{broken")


@pytest.mark.parametrize("raw", [None, "", "[]", [], '["   "]', '{"name":"x"}'])
def test_producers_are_required_and_must_be_valid(raw):
    with pytest.raises(
        ReleaseValidationError,
        match="producers_(required|empty|invalid)",
    ):
        normalize_required_names(raw, "producers")


def test_producer_duplicates_are_rejected():
    with pytest.raises(ReleaseValidationError, match="producers_duplicate"):
        normalize_required_names('["Producer", " producer "]', "producers")
