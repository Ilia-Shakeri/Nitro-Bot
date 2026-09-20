import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs as _parse_qs
from urllib.parse import urlparse as _urlparse


class DmbJob:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def format_dmb_date(self, value: str) -> str:
        try:
            return date.fromisoformat(value).strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            raise ValueError("dmb_job_date_invalid") from None

    def load_dmb_job(self, path: str) -> dict:
        job_path = Path(path).resolve()
        job = json.loads(job_path.read_text(encoding="utf-8"))
        if not isinstance(job, dict) or job.get("schema_version") != 2:
            raise ValueError("dmb_job_schema_invalid")
        if job.get("mode") != "create":
            raise ValueError("dmb_job_mode_invalid")
        producers = job.get("producers")
        if isinstance(producers, str):
            producers = json.loads(producers)
            job["producers"] = producers
        for field in (
            "artists",
            "producers",
            "legal_names",
            "artist_mappings",
            "contributors",
        ):
            if not isinstance(job.get(field), list):
                raise ValueError(f"dmb_job_{field}_invalid")
        for field in (
            "release_id",
            "song_name",
            "release_date",
            "genre",
            "dmb_genre",
            "label",
            "metadata_language",
            "expiration_date",
            "price_code",
            "itunes_price_code",
            "c_line_year",
            "p_line_year",
            "cover_path",
            "track_path",
        ):
            if job.get(field) in (None, ""):
                raise ValueError(f"dmb_job_{field}_invalid")
        if any(
            not isinstance(item, dict)
            or not str(item.get("name", "")).strip()
            or not isinstance(item.get("has_account"), bool)
            or item.get("role") != "Performer"
            for item in job["contributors"]
        ):
            raise ValueError("dmb_job_contributors_invalid")
        if (
            job["label"] != "Mitrxv"
            or job["metadata_language"] != "English"
            or job["expiration_date"] != "2099-12-31"
            or job["price_code"] != "MA"
            or job["itunes_price_code"] != "14"
            or not re.fullmatch(r"\d{4}", str(job["c_line_year"]))
            or not re.fullmatch(r"\d{4}", str(job["p_line_year"]))
        ):
            raise ValueError("dmb_job_fixed_values_invalid")
        cover_path = Path(job["cover_path"]).resolve()
        track_path = Path(job["track_path"]).resolve()
        if (
            cover_path.parent != job_path.parent
            or track_path.parent != job_path.parent
            or cover_path.suffix.lower() not in {".jpg", ".jpeg"}
            or track_path.suffix.lower() != ".wav"
        ):
            raise ValueError("dmb_job_media_path_invalid")
        return job

    def extract_dmb_release_id(self, url: str) -> str:
        parsed = _urlparse(url)
        query = _parse_qs(parsed.query)
        for key in ("releaseId", "albumId", "id"):
            values = query.get(key)
            if values and re.fullmatch(r"(?=[A-Za-z0-9._:-]{1,128}$)(?=.*\d)[A-Za-z0-9._:-]+", values[0]):
                return values[0]
        ignored = {"album", "albums", "edit", "music", "release", "releases"}
        for part in reversed([value for value in parsed.path.split("/") if value]):
            if part.lower() not in ignored and re.fullmatch(r"(?=[A-Za-z0-9._:-]{1,128}$)(?=.*\d)[A-Za-z0-9._:-]+", part):
                return part
        raise ValueError("dmb_release_id_not_found")

    def write_dmb_result(
        self,
        path: str,
        release_id: int,
        dmb_release_id: str,
        ean_upc: str,
        isrc: str,
        current_url: str,
        screenshot_path: str,
    ) -> None:
        parsed_url = _urlparse(current_url)
        allowed_host = os.getenv("DMB_ALLOWED_HOST", "dmb.kontornewmedia.com").lower()
        if parsed_url.scheme != "https" or parsed_url.hostname != allowed_host:
            raise ValueError("dmb_result_url_invalid")
        if self.extract_dmb_release_id(current_url) != str(dmb_release_id).strip():
            raise ValueError("dmb_result_release_id_mismatch")
        payload = {
            "submitted": True,
            "release_id": int(release_id),
            "dmb_release_id": str(dmb_release_id).strip(),
            "ean_upc": str(ean_upc).strip(),
            "isrcs": [str(isrc).strip().upper()],
            "current_url": current_url,
            "screenshot_path": screenshot_path,
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        temporary.replace(target)

    def write_submit_checkpoint(
        self,
        path: str,
        release_id: int,
        ean_upc: str,
        isrc: str,
        title: str,
    ) -> None:
        ean = str(ean_upc).strip()
        normalized_isrc = str(isrc).strip().upper()
        normalized_title = str(title).strip()
        if not re.fullmatch(r"\d{8,14}", ean):
            raise ValueError("dmb_checkpoint_ean_invalid")
        if not re.fullmatch(r"[A-Z0-9-]{8,20}", normalized_isrc):
            raise ValueError("dmb_checkpoint_isrc_invalid")
        if not normalized_title or len(normalized_title) > 255:
            raise ValueError("dmb_checkpoint_title_invalid")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "release_id": int(release_id),
                    "ean_upc": ean,
                    "isrcs": [normalized_isrc],
                    "title": normalized_title,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )
        temporary.replace(target)


_library = DmbJob()


def format_dmb_date(value: str) -> str:
    return _library.format_dmb_date(value)


def load_dmb_job(path: str) -> dict:
    return _library.load_dmb_job(path)


def extract_dmb_release_id(url: str) -> str:
    return _library.extract_dmb_release_id(url)


def write_dmb_result(
    path: str,
    release_id: int,
    dmb_release_id: str,
    ean_upc: str,
    isrc: str,
    current_url: str,
    screenshot_path: str,
) -> None:
    _library.write_dmb_result(
        path,
        release_id,
        dmb_release_id,
        ean_upc,
        isrc,
        current_url,
        screenshot_path,
    )


def write_submit_checkpoint(
    path: str,
    release_id: int,
    ean_upc: str,
    isrc: str,
    title: str,
) -> None:
    _library.write_submit_checkpoint(path, release_id, ean_upc, isrc, title)
