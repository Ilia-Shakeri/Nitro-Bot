"""Build the exact DMB-facing values from a release contract."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


LABEL = "Mitrxv"
LANGUAGE = "English"
EXPIRATION_DATE = "2099-12-31"
PRICE_CODE = "MA"
ITUNES_PRICE_CODE = "14"

_LOCAL_GENRES = Path(__file__).parents[1] / "shared" / "release-genres.json"
_CONTAINER_GENRES = Path("/shared/release-genres.json")
_GENRE_PATH = _LOCAL_GENRES if _LOCAL_GENRES.is_file() else _CONTAINER_GENRES
_GENRE_TREE: dict[str, list[str]] = json.loads(_GENRE_PATH.read_text(encoding="utf-8"))

_LEGACY_GENRE_MAP: dict[str, dict[str | None, str]] = {
    "HipHop / Rap [Urban]": {
        None: "HipHop / Rap [Urban]",
        "Trap": "HipHop / Rap [Urban]",
        "Drill": "HipHop / Rap [Urban]",
        "Boom Bap": "HipHop / Rap [Urban]",
        "Gangsta Rap": "HipHop / Rap [Urban]",
        "Conscious": "HipHop / Rap [Urban]",
        "Cloud Rap": "HipHop / Rap [Urban]",
    },
    "Pop": {
        None: "Pop",
        "Dance Pop": "Pop",
        "Synth Pop": "Pop",
        "Indie Pop": "Pop",
        "Electropop": "Pop",
        "K-Pop": "Pop",
    },
    "Rock": {
        None: "Rock / Rockpop",
        "Alternative": "Alternative [Rock / Rockpop]",
        "Indie Rock": "International [Rock / Rockpop]",
        "Hard Rock": "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
        "Punk": "Alternative [Rock / Rockpop]",
        "Post-Rock": "Progressive Rock [Rock / Rockpop]",
    },
    "Electronic / Dance": {
        None: "Dance & Electronic",
        "House": "Dance & Electronic",
        "Techno": "Dance & Electronic",
        "Trance": "Dance & Electronic",
        "Dubstep": "Dance & Electronic",
        "Drum & Bass": "Dance & Electronic",
        "EDM": "Dance & Electronic",
    },
    "R&B / Soul": {
        None: "Rhythm and Blues [Urban]",
        "Contemporary R&B": "Rhythm and Blues [Urban]",
        "Neo-Soul": "Soul [Urban]",
        "Funk": "Funk [Urban]",
    },
    "Classical": {
        None: "Classical",
        "Orchestral": "Classical Music Instrumental [Classical]",
        "Piano": "Classical Music Instrumental [Classical]",
        "Opera": "Classic - Vocal [Classical]",
        "Chamber": "Chamber Music [Classical]",
    },
    "Jazz": {
        None: "Jazz",
        "Smooth Jazz": "Modern [Jazz]",
        "Bebop": "Modern [Jazz]",
        "Fusion": "Modern [Jazz]",
        "Swing": "Traditional / Swing [Jazz]",
    },
    "Folk": {
        None: "Worldmusic / Folklore / Folk Music",
        "Indie Folk": "Worldmusic / Folklore / Folk Music",
        "Singer-Songwriter": "Singer / Songwriter [Rock / Rockpop]",
        "Americana": "Americana [Country and Western]",
    },
    "Country": {
        None: "Country and Western",
        "Modern Country": "Mainstream [Country and Western]",
        "Bluegrass": "Bluegrass [Country and Western]",
        "Country Pop": "Mainstream [Country and Western]",
    },
    "Reggae": {
        None: "Reggae [Urban]",
        "Roots": "Reggae [Urban]",
        "Dancehall": "Reggae [Urban]",
        "Dub": "Reggae [Urban]",
    },
    "Metal": {
        None: "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
        "Heavy Metal": "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
        "Death Metal": "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
        "Black Metal": "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
        "Metalcore": "Metal (Hard 'n' Heavy) [Rock / Rockpop]",
    },
    "World": {
        None: "Worldmusic / Folklore / Folk Music",
        "Latin": "Worldmusic / Folklore / Folk Music",
        "Afrobeat": "Worldmusic / Folklore / Folk Music",
        "Persian": "Worldmusic / Folklore / Folk Music",
        "Arabic": "Worldmusic / Folklore / Folk Music",
    },
}


def dmb_genre_text(genre: str, sub_genre: str | None) -> str:
    legacy = _LEGACY_GENRE_MAP.get(genre)
    if legacy is not None and sub_genre in legacy:
        return legacy[sub_genre]
    choices = _GENRE_TREE.get(genre)
    if choices is not None:
        if sub_genre is None:
            return genre
        if sub_genre not in choices:
            raise ValueError("dmb_sub_genre_not_mapped")
        return f"{sub_genre} [{genre}]"
    if legacy is None:
        raise ValueError("dmb_genre_not_mapped")
    if sub_genre not in legacy:
        raise ValueError("dmb_sub_genre_not_mapped")
    return legacy[sub_genre]


def copyright_years(
    *,
    is_rerelease: bool,
    original_release_date: str | None,
    current_year: int | None = None,
) -> tuple[str, str]:
    year = current_year or date.today().year
    if not 2000 <= year <= 2099:
        raise ValueError("dmb_current_year_invalid")
    p_year = str(year)
    if not is_rerelease:
        return p_year, p_year
    try:
        c_year = str(date.fromisoformat(original_release_date or "").year)
    except ValueError:
        raise ValueError("dmb_original_release_date_invalid") from None
    return c_year, p_year


def contributor_contract(
    artists: list[dict], artist_mappings: list[dict]
) -> list[dict]:
    mappings = {
        str(mapping.get("artist_name", "")).strip().casefold(): mapping
        for mapping in artist_mappings
        if isinstance(mapping, dict)
    }
    contributors: list[dict] = []
    for artist in artists:
        name = str(artist.get("name", "")).strip()
        mapping = mappings.get(name.casefold())
        if not name or mapping is None:
            raise ValueError("dmb_contributor_mapping_missing")
        has_account = mapping.get("dmb_has_account")
        if not isinstance(has_account, bool):
            raise ValueError("dmb_contributor_mapping_invalid")
        contributors.append(
            {
                "name": name,
                "has_account": has_account,
                "role": "Performer",
            }
        )
    if not contributors:
        raise ValueError("dmb_contributors_missing")
    return contributors
