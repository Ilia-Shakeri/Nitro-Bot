from datetime import date

import pytest

from release_validation import (
    ReleaseValidationError,
    legacy_artist_name,
    normalize_artist_mappings,
    normalize_artists,
    normalize_english_text,
    normalize_names,
    normalize_required_names,
    normalize_submission_id,
    validate_genre,
    validate_notice_payload_size,
    validate_release_mapping,
    validate_release_dates,
    validate_policy_acceptance,
)

TODAY = date(2026, 7, 26)


def test_policy_acceptance_requires_explicit_true():
    for value in (None, False):
        with pytest.raises(ReleaseValidationError, match="policy_acceptance_required"):
            validate_policy_acceptance(value)
    validate_policy_acceptance(True)


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


def test_artist_list_requires_one_to_three_primary():
    with pytest.raises(ReleaseValidationError, match="artists_primary_required"):
        normalize_artists(
            [
                {"name": "One", "role": "featured"},
                {"name": "Two", "role": "featured"},
            ]
        )
    assert len(normalize_artists(
        [
            {"name": "One", "role": "primary"},
            {"name": "Two", "role": "primary"},
        ]
    )) == 2
    with pytest.raises(ReleaseValidationError, match="artists_primary_max"):
        normalize_artists(
            [
                {"name": "One", "role": "primary"},
                {"name": "Two", "role": "primary"},
                {"name": "Three", "role": "primary"},
                {"name": "Four", "role": "primary"},
            ]
        )


@pytest.mark.parametrize("count", range(1, 7))
def test_one_through_six_artists_are_accepted(count):
    artists = normalize_artists([
        {"name": f"Artist {index}", "role": "primary" if index == 0 else "featured"}
        for index in range(count)
    ])
    assert len(artists) == count


def test_seventh_artist_is_rejected():
    with pytest.raises(ReleaseValidationError, match="artists_max"):
        normalize_artists([
            {"name": f"Artist {index}", "role": "primary" if index == 0 else "featured"}
            for index in range(7)
        ])


def test_legacy_artist_name_keeps_all_primary_artists_in_order():
    assert legacy_artist_name([
        {"name": "One", "role": "primary"},
        {"name": "Two", "role": "primary"},
        {"name": "Guest", "role": "featured"},
    ]) == "One, Two feat. Guest"


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


def test_mapping_requires_platform_link_for_existing_profile():
    with pytest.raises(ReleaseValidationError, match="mapping_required"):
        validate_release_mapping(
            requires_new_profile=False,
            profile_email=None,
            mapping_spotify=" ",
            mapping_apple=None,
        )


@pytest.mark.parametrize(
    ("spotify", "apple"),
    [
        (" https://open.spotify.com/artist/abc123 ", None),
        (None, " https://music.apple.com/us/artist/name/123456 "),
    ],
)
def test_mapping_accepts_one_platform_link(spotify, apple):
    _, normalized_spotify, normalized_apple = validate_release_mapping(
        requires_new_profile=False,
        profile_email=None,
        mapping_spotify=spotify,
        mapping_apple=apple,
    )
    assert normalized_spotify == (spotify.strip() if spotify else None)
    assert normalized_apple == (apple.strip() if apple else None)


def test_new_profile_mapping_requires_email():
    with pytest.raises(ReleaseValidationError, match="profile_email_required"):
        validate_release_mapping(
            requires_new_profile=True,
            profile_email=None,
            mapping_spotify=None,
            mapping_apple=None,
        )

    email, spotify, apple = validate_release_mapping(
        requires_new_profile=True,
        profile_email=" artist@example.com ",
        mapping_spotify=None,
        mapping_apple=None,
    )
    assert email == "artist@example.com"
    assert spotify is None
    assert apple is None


@pytest.mark.parametrize("value", ["آهنگ", "Песня", "Song 🎵", ""])
def test_non_english_release_text_is_rejected(value):
    with pytest.raises(ReleaseValidationError, match="english_only_input"):
        normalize_english_text(value)


def test_release_text_length_is_bounded():
    assert normalize_english_text("A" * 200, "song_name") == "A" * 200
    with pytest.raises(ReleaseValidationError, match="song_name_too_long"):
        normalize_english_text("A" * 201, "song_name")


@pytest.mark.parametrize("value", ["", "../bad", "bad/id", " bad id ", "x" * 65])
def test_submission_id_rejects_unsafe_values(value):
    with pytest.raises(ReleaseValidationError, match="submission_id_invalid"):
        normalize_submission_id(value)


def test_submission_id_accepts_client_token_shape():
    assert normalize_submission_id("release_1234-AB.cd:1") == "release_1234-AB.cd:1"


def test_genre_and_subgenre_pair_is_enforced():
    assert validate_genre(" Urban ", "HipHop / Rap") == ("Urban", "HipHop / Rap")
    assert validate_genre("Pop", "") == ("Pop", None)
    assert validate_genre("Pop", "Synth Pop") == ("Pop", None)
    assert validate_genre("Rock", "Punk") == ("Rock / Rockpop", "Alternative")
    with pytest.raises(ReleaseValidationError, match="genre_invalid"):
        validate_genre("Made Up", None)
    with pytest.raises(ReleaseValidationError, match="sub_genre_invalid"):
        validate_genre("Pop", "Techno")


def test_name_list_count_and_payload_size_are_bounded():
    with pytest.raises(ReleaseValidationError, match="producers_max"):
        normalize_names([f"Name {index}" for index in range(21)], "producers")
    with pytest.raises(ReleaseValidationError, match="producers_too_large"):
        normalize_names("[" + " " * 32_768 + "]", "producers")


def test_notice_dynamic_payload_is_bounded():
    with pytest.raises(ReleaseValidationError, match="release_metadata_too_large"):
        validate_notice_payload_size(
            song_name="Song",
            artists=[{"name": "Artist", "role": "primary"}],
            producers=["P" * 200] * 15,
            legal_names=["Legal"],
            genre="Pop",
            sub_genre=None,
            artist_mappings=[],
        )


@pytest.mark.parametrize(
    "mapping",
    [
        {"spotify_url": "https://spotify.example/artist/abc"},
        {"spotify_url": "https://open.spotify.com/album/abc"},
        {"spotify_url": "https://open.spotify.com:444/artist/abc"},
        {"apple_music_url": "https://apple.example/us/artist/name/123"},
        {"apple_music_url": "https://music.apple.com/us/album/name/123"},
        {"apple_music_url": "https://music.apple.com/us/artist/name/not-a-number"},
    ],
)
def test_artist_mapping_rejects_wrong_platform_links(mapping):
    payload = {
        "artist_name": "One",
        "requires_new_profile": False,
        **mapping,
    }
    with pytest.raises(ReleaseValidationError, match="artist_mapping_url_invalid"):
        normalize_artist_mappings(
            [payload],
            [{"name": "One", "role": "primary"}],
        )


def test_artist_mapping_accepts_real_platform_link_shapes():
    artists = [{"name": "One", "role": "primary"}]
    spotify = normalize_artist_mappings(
        [{
            "artist_name": "One",
            "requires_new_profile": False,
            "spotify_url": "https://open.spotify.com/artist/abc123",
        }],
        artists,
    )
    apple = normalize_artist_mappings(
        [{
            "artist_name": "One",
            "requires_new_profile": False,
            "apple_music_url": "https://music.apple.com/us/artist/one/123456",
        }],
        artists,
    )
    assert spotify[0]["spotify_url"].endswith("/abc123")
    assert apple[0]["apple_music_url"].endswith("/123456")
    assert spotify[0]["dmb_has_account"] is False


def test_artist_mapping_keeps_explicit_dmb_account_state():
    mappings = normalize_artist_mappings(
        [{
            "artist_name": "One",
            "requires_new_profile": False,
            "dmb_has_account": True,
            "spotify_url": "https://open.spotify.com/artist/one",
        }],
        [{"name": "One", "role": "primary"}],
    )
    assert mappings[0]["dmb_has_account"] is True

    with pytest.raises(ReleaseValidationError, match="artist_mappings_invalid"):
        normalize_artist_mappings(
            [{
                "artist_name": "One",
                "requires_new_profile": False,
                "dmb_has_account": "yes",
                "spotify_url": "https://open.spotify.com/artist/one",
            }],
            [{"name": "One", "role": "primary"}],
        )


def test_artist_mappings_require_one_complete_record_per_artist():
    artists = normalize_artists([
        {"name": "One", "role": "primary"},
        {"name": "Two", "role": "featured"},
    ])
    mappings = normalize_artist_mappings([
        {
            "artist_name": "one",
            "requires_new_profile": False,
            "spotify_url": "https://open.spotify.com/artist/one",
        },
        {
            "artist_name": "Two",
            "requires_new_profile": True,
            "profile_email": "two@example.com",
        },
    ], artists)
    assert [item["artist_name"] for item in mappings] == ["One", "Two"]

    with pytest.raises(ReleaseValidationError, match="artist_mappings_incomplete"):
        normalize_artist_mappings(mappings[:1], artists)


@pytest.mark.parametrize(
    ("mappings", "error"),
    [
        (
            [
                {"artist_name": "One", "requires_new_profile": False, "spotify_url": "https://open.spotify.com/artist/a"},
                {"artist_name": "one", "requires_new_profile": False, "spotify_url": "https://open.spotify.com/artist/b"},
            ],
            "artist_mapping_duplicate",
        ),
        (
            [
                {"artist_name": "One", "requires_new_profile": False, "spotify_url": "https://open.spotify.com/artist/a"},
                {"artist_name": "Unknown", "requires_new_profile": False, "spotify_url": "https://open.spotify.com/artist/b"},
            ],
            "artist_mapping_unknown_artist",
        ),
    ],
)
def test_duplicate_and_unknown_mappings_are_rejected(mappings, error):
    artists = normalize_artists([
        {"name": "One", "role": "primary"},
        {"name": "Two", "role": "featured"},
    ])
    with pytest.raises(ReleaseValidationError, match=error):
        normalize_artist_mappings(mappings, artists)


def test_legacy_single_artist_mapping_fallback():
    artists = normalize_artists([{"name": "One", "role": "primary"}])
    mappings = normalize_artist_mappings(
        None,
        artists,
        legacy_mapping_spotify="https://open.spotify.com/artist/one",
    )
    assert mappings[0]["spotify_url"].endswith("/one")
