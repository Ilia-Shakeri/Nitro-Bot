import json
from pathlib import Path

_GENRE_FILE = Path(__file__).parents[1] / "shared" / "release-genres.json"
_RAW_GENRES = json.loads(_GENRE_FILE.read_text(encoding="utf-8"))
if not isinstance(_RAW_GENRES, dict) or not all(
    isinstance(genre, str)
    and isinstance(sub_genres, list)
    and all(isinstance(sub_genre, str) for sub_genre in sub_genres)
    for genre, sub_genres in _RAW_GENRES.items()
):
    raise RuntimeError("release_genres_invalid")

GENRE_TREE: dict[str, frozenset[str]] = {
    genre: frozenset(sub_genres) for genre, sub_genres in _RAW_GENRES.items()
}
