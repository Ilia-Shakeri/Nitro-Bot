"""Lease-based bridge from the internal release API to DMB browser delivery."""

import json
import hashlib
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3
import requests
from PIL import Image, ImageOps

from dmb_contract import (
    EXPIRATION_DATE,
    ITUNES_PRICE_CODE,
    LABEL,
    LANGUAGE,
    PRICE_CODE,
    contributor_contract,
    copyright_years,
    dmb_genre_text,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000").rstrip("/")
SECRET = os.getenv("SELENIUM_SECRET_KEY", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "nitro-bot")
POLL_INTERVAL = max(2, int(os.getenv("POLL_INTERVAL", "30")))
HEARTBEAT_INTERVAL = max(10, int(os.getenv("DMB_HEARTBEAT_SECONDS", "60")))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
CREATE_ENABLED = os.getenv("DMB_CREATE_ENABLED", "false").lower() == "true"
EDIT_ENABLED = os.getenv("DMB_EDIT_ENABLED", "false").lower() == "true"
DMB_USERNAME = os.getenv("DMB_USERNAME", "")
DMB_PASSWORD = os.getenv("DMB_PASSWORD", "")
DMB_ALLOWED_HOST = os.getenv("DMB_ALLOWED_HOST", "dmb.kontornewmedia.com").lower()
WORKER_ID = os.getenv("DMB_WORKER_ID", f"{socket.gethostname()}:{os.getpid()}")
CIRCUIT_FAILURE_LIMIT = max(1, int(os.getenv("DMB_CIRCUIT_FAILURES", "3")))

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
RESULTS_DIR = BASE_DIR / "results"
CREATE_SUITE = BASE_DIR / "automation" / "create_album.robot"
CIRCUIT_STATE_PATH = RESULTS_DIR / "dmb-circuit.json"
_WORKER_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_DMB_ID_RE = re.compile(r"^(?=[A-Za-z0-9._:-]{1,128}$)(?=.*\d)[A-Za-z0-9._:-]+$")
_EAN_RE = re.compile(r"^\d{8,14}$")
_ISRC_RE = re.compile(r"^[A-Z0-9-]{8,20}$")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("dmb-automation")

_s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="us-east-1",
)
_http = requests.Session()
_http.headers.update(
    {
        "Authorization": f"Bearer {SECRET}",
        "X-DMB-Worker-ID": WORKER_ID,
    }
)


class DeliveryError(RuntimeError):
    pass


def validate_config() -> None:
    if not SECRET:
        raise DeliveryError("SELENIUM_SECRET_KEY_missing")
    if not _WORKER_ID_RE.fullmatch(WORKER_ID):
        raise DeliveryError("DMB_WORKER_ID_invalid")
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        raise DeliveryError("S3_credentials_missing")
    if not DMB_USERNAME or not DMB_PASSWORD:
        raise DeliveryError("DMB_credentials_missing")
    if DRY_RUN:
        raise DeliveryError("DRY_RUN_cannot_claim_live_jobs")
    if EDIT_ENABLED:
        raise DeliveryError("DMB_edit_path_not_ready")
    if not CREATE_ENABLED:
        raise DeliveryError("DMB_create_disabled")


def get_pending(mode: str = "create") -> list[dict]:
    response = _http.get(
        f"{API_BASE_URL}/internal/releases/pending",
        params={"mode": mode},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) > 1:
        raise DeliveryError("pending_response_invalid")
    return payload


def heartbeat(release_id: int) -> None:
    response = _http.post(
        f"{API_BASE_URL}/internal/releases/{release_id}/heartbeat",
        timeout=30,
    )
    response.raise_for_status()


def set_status(
    release_id: int,
    status: str,
    *,
    result: dict | None = None,
    checkpoint: dict | None = None,
    error: str | None = None,
) -> None:
    data = {"status": status}
    if result is not None:
        data.update(
            {
                "dmb_release_id": result["dmb_release_id"],
                "ean_upc": result["ean_upc"],
                "isrcs_json": json.dumps(result["isrcs"]),
                "evidence_path": result["evidence_path"],
                "submission_fingerprint": result["submission_fingerprint"],
            }
        )
    if error:
        data["error"] = error[:2000]
    if status == "uncertain":
        data["evidence_path"] = f"results/{release_id}"
        if checkpoint is not None:
            data.update(
                {
                    "ean_upc": checkpoint["ean_upc"],
                    "isrcs_json": json.dumps(checkpoint["isrcs"]),
                    "submission_fingerprint": checkpoint["submission_fingerprint"],
                }
            )
    response = _http.post(
        f"{API_BASE_URL}/internal/releases/{release_id}/status",
        data=data,
        timeout=30,
    )
    response.raise_for_status()


def _validated_release_id(value: object) -> int:
    if isinstance(value, bool):
        raise DeliveryError("release_id_invalid")
    try:
        release_id = int(value)
    except (TypeError, ValueError):
        raise DeliveryError("release_id_invalid") from None
    if release_id <= 0:
        raise DeliveryError("release_id_invalid")
    return release_id


def validate_release_contract(release: dict) -> None:
    required = {
        "id",
        "user_id",
        "song_name",
        "artists",
        "producers",
        "legal_names",
        "release_date",
        "is_rerelease",
        "genre",
        "track_url",
        "cover_url",
        "artist_mappings",
        "is_edit",
        "copyright_requested",
        "explicit_content",
    }
    if not isinstance(release, dict) or required.difference(release):
        raise DeliveryError("release_contract_incomplete")
    _validated_release_id(release["id"])
    if release["is_edit"]:
        if not release.get("source_release_id") or not release.get("source_dmb_release_id"):
            raise DeliveryError("edit_source_evidence_missing")
    for field in ("song_name", "release_date", "genre", "track_url", "cover_url"):
        if not isinstance(release[field], str) or not release[field].strip():
            raise DeliveryError(f"release_{field}_invalid")
    for field in ("artists", "legal_names", "artist_mappings"):
        if not isinstance(release[field], list) or not release[field]:
            raise DeliveryError(f"release_{field}_invalid")


def download(key: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _s3.download_file(S3_BUCKET, key, str(destination))
    return destination


def prepare_cover_for_dmb(source: Path, destination: Path) -> Path:
    try:
        with Image.open(source) as image:
            output = ImageOps.fit(
                image.convert("RGB"),
                (3000, 3000),
                method=Image.Resampling.LANCZOS,
            )
            output.save(destination, format="JPEG", quality=95, optimize=True)
    except (OSError, ValueError):
        raise DeliveryError("dmb_cover_invalid") from None
    with Image.open(destination) as verified:
        if verified.format != "JPEG" or verified.size != (3000, 3000):
            raise DeliveryError("dmb_cover_invalid")
    return destination


def validate_track_for_dmb(path: Path) -> Path:
    try:
        header = path.read_bytes()[:12]
    except OSError:
        raise DeliveryError("dmb_track_invalid") from None
    if len(header) < 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise DeliveryError("dmb_track_must_be_wav")
    return path


def build_job_payload(release: dict, cover_path: Path, track_path: Path) -> dict:
    validate_release_contract(release)
    c_line_year, p_line_year = copyright_years(
        is_rerelease=release["is_rerelease"],
        original_release_date=release.get("original_release_date"),
    )
    return {
        "schema_version": 2,
        "release_id": _validated_release_id(release["id"]),
        "mode": "edit" if release["is_edit"] else "create",
        "source_release_id": release.get("source_release_id"),
        "source_dmb_release_id": release.get("source_dmb_release_id"),
        "song_name": release["song_name"],
        "artists": release["artists"],
        "producers": release.get("producers") or "[]",
        "legal_names": release["legal_names"],
        "release_date": release["release_date"],
        "is_rerelease": release["is_rerelease"],
        "original_release_date": release.get("original_release_date"),
        "genre": release["genre"],
        "sub_genre": release.get("sub_genre"),
        "dmb_genre": dmb_genre_text(release["genre"], release.get("sub_genre")),
        "label": LABEL,
        "metadata_language": LANGUAGE,
        "expiration_date": EXPIRATION_DATE,
        "price_code": PRICE_CODE,
        "itunes_price_code": ITUNES_PRICE_CODE,
        "c_line_year": c_line_year,
        "p_line_year": p_line_year,
        "contributors": contributor_contract(
            release["artists"], release["artist_mappings"]
        ),
        "artist_mappings": release["artist_mappings"],
        "copyright_requested": release["copyright_requested"],
        "explicit_content": release["explicit_content"],
        "cover_path": str(cover_path.resolve()),
        "track_path": str(track_path.resolve()),
    }


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def read_circuit_state() -> dict:
    if not CIRCUIT_STATE_PATH.exists():
        return {"open": False, "failures": 0}
    try:
        state = json.loads(CIRCUIT_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"open": True, "failures": CIRCUIT_FAILURE_LIMIT, "reason": "state_invalid"}
    if (
        not isinstance(state, dict)
        or not isinstance(state.get("open"), bool)
        or not isinstance(state.get("failures"), int)
        or state["failures"] < 0
    ):
        return {"open": True, "failures": CIRCUIT_FAILURE_LIMIT, "reason": "state_invalid"}
    return state


def record_delivery_outcome(release_id: int, outcome: str) -> bool:
    if outcome == "completed":
        if CIRCUIT_STATE_PATH.exists():
            CIRCUIT_STATE_PATH.unlink()
        return False
    previous = read_circuit_state()
    failures = int(previous.get("failures", 0)) + 1
    open_circuit = outcome in {"uncertain", "report_failed"} or failures >= CIRCUIT_FAILURE_LIMIT
    write_json_atomic(
        CIRCUIT_STATE_PATH,
        {
            "open": open_circuit,
            "failures": failures,
            "release_id": release_id,
            "outcome": outcome,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return open_circuit


def load_result(path: Path, release_id: int) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise DeliveryError("dmb_result_missing_or_invalid") from None
    if (
        not isinstance(result, dict)
        or result.get("submitted") is not True
        or result.get("release_id") != release_id
        or not _DMB_ID_RE.fullmatch(str(result.get("dmb_release_id", "")))
        or not _EAN_RE.fullmatch(str(result.get("ean_upc", "")))
        or not isinstance(result.get("isrcs"), list)
        or not result["isrcs"]
        or any(not isinstance(code, str) or not _ISRC_RE.fullmatch(code) for code in result["isrcs"])
    ):
        raise DeliveryError("dmb_result_evidence_invalid")
    current_url = str(result.get("current_url", ""))
    screenshot = Path(str(result.get("screenshot_path", ""))).resolve()
    parsed_url = urlparse(current_url)
    expected_output = (RESULTS_DIR / str(release_id)).resolve()
    try:
        screenshot_header = screenshot.read_bytes()[:8]
        screenshot_size = screenshot.stat().st_size
    except OSError:
        screenshot_header = b""
        screenshot_size = 0
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != DMB_ALLOWED_HOST
        or str(result["dmb_release_id"]) not in current_url
        or not screenshot.is_file()
        or not screenshot.is_relative_to(expected_output)
        or screenshot_header != b"\x89PNG\r\n\x1a\n"
        or screenshot_size < 100
    ):
        raise DeliveryError("dmb_result_evidence_invalid")
    result["evidence_path"] = f"results/{release_id}"
    return result


def submission_fingerprint(
    release_id: int,
    title: str,
    ean_upc: str,
    isrcs: list[str],
) -> str:
    value = json.dumps(
        {
            "release_id": release_id,
            "title": title,
            "ean_upc": ean_upc,
            "isrcs": isrcs,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_submit_checkpoint(path: Path, release_id: int, expected_title: str) -> dict:
    try:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(checkpoint, dict):
            raise ValueError
        started_at = datetime.fromisoformat(str(checkpoint.get("started_at", "")))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        raise DeliveryError("dmb_submit_checkpoint_invalid") from None
    ean = str(checkpoint.get("ean_upc", "")).strip()
    isrcs = checkpoint.get("isrcs")
    title = str(checkpoint.get("title", "")).strip()
    if (
        checkpoint.get("release_id") != release_id
        or title != expected_title
        or not _EAN_RE.fullmatch(ean)
        or not isinstance(isrcs, list)
        or not isrcs
        or any(not isinstance(code, str) or not _ISRC_RE.fullmatch(code) for code in isrcs)
        or started_at.tzinfo is None
    ):
        raise DeliveryError("dmb_submit_checkpoint_invalid")
    checkpoint["ean_upc"] = ean
    checkpoint["isrcs"] = isrcs
    checkpoint["submission_fingerprint"] = submission_fingerprint(
        release_id,
        title,
        ean,
        isrcs,
    )
    return checkpoint


def bind_result_to_checkpoint(result: dict, checkpoint: dict) -> dict:
    if (
        result["ean_upc"] != checkpoint["ean_upc"]
        or result["isrcs"] != checkpoint["isrcs"]
    ):
        raise DeliveryError("dmb_result_checkpoint_mismatch")
    return {**result, "submission_fingerprint": checkpoint["submission_fingerprint"]}


def run_robot(
    release_id: int,
    job_file: Path,
    result_file: Path,
    checkpoint_file: Path,
    expected_title: str,
) -> dict:
    if result_file.exists():
        result_file.unlink()
    if checkpoint_file.exists():
        checkpoint_file.unlink()
    output_dir = RESULTS_DIR / str(release_id)
    env = {
        **os.environ,
        "DMB_USERNAME": DMB_USERNAME,
        "DMB_PASSWORD": DMB_PASSWORD,
        "DMB_JOB_FILE": str(job_file),
        "DMB_RESULT_FILE": str(result_file),
        "DMB_SUBMIT_CHECKPOINT": str(checkpoint_file),
        "DMB_SUBMIT_ENABLED": "true",
    }
    command = [
        "xvfb-run",
        "-a",
        "robot",
        "--outputdir",
        str(output_dir),
        str(CREATE_SUITE),
    ]
    process = subprocess.Popen(command, cwd=str(BASE_DIR), env=env)
    next_heartbeat = time.monotonic() + HEARTBEAT_INTERVAL
    while process.poll() is None:
        time.sleep(1)
        if time.monotonic() < next_heartbeat:
            continue
        try:
            heartbeat(release_id)
        except Exception:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            raise DeliveryError("dmb_lease_heartbeat_failed") from None
        next_heartbeat = time.monotonic() + HEARTBEAT_INTERVAL
    if process.returncode != 0:
        raise DeliveryError(f"robot_exit_{process.returncode}")
    result = load_result(result_file, release_id)
    checkpoint = load_submit_checkpoint(checkpoint_file, release_id, expected_title)
    return bind_result_to_checkpoint(result, checkpoint)


def _safe_job_dir(release_id: int) -> Path:
    root = DOWNLOAD_DIR.resolve()
    job_dir = (root / str(release_id)).resolve()
    if job_dir.parent != root:
        raise DeliveryError("job_directory_invalid")
    return job_dir


def process_release(release: dict) -> str:
    release_id = _validated_release_id(release.get("id") if isinstance(release, dict) else None)
    job_dir = _safe_job_dir(release_id)
    result_file = RESULTS_DIR / str(release_id) / "result.json"
    checkpoint_file = RESULTS_DIR / str(release_id) / "submit-started.json"
    try:
        validate_release_contract(release)
        if release["is_edit"]:
            raise DeliveryError("DMB_edit_path_not_ready")
        if job_dir.exists():
            shutil.rmtree(job_dir)
        job_dir.mkdir(parents=True)
        source_cover = download(release["cover_url"], job_dir / "source-cover")
        cover = prepare_cover_for_dmb(source_cover, job_dir / "cover.jpg")
        track = validate_track_for_dmb(
            download(release["track_url"], job_dir / "track.wav")
        )
        job_file = job_dir / "job.json"
        write_json_atomic(job_file, build_job_payload(release, cover, track))
        result = run_robot(
            release_id,
            job_file,
            result_file,
            checkpoint_file,
            release["song_name"],
        )
        set_status(release_id, "completed", result=result)
        log.info("release %s completed with verified DMB evidence", release_id)
        return "completed"
    except Exception as exc:
        reason = f"{type(exc).__name__}:{exc}"[:2000]
        log.exception("release %s delivery failed", release_id)
        try:
            state = "uncertain" if checkpoint_file.exists() else "retry"
            checkpoint = None
            if state == "uncertain":
                try:
                    checkpoint = load_submit_checkpoint(
                        checkpoint_file,
                        release_id,
                        release["song_name"],
                    )
                except DeliveryError as checkpoint_error:
                    reason = f"{reason};{checkpoint_error}"[:2000]
            set_status(release_id, state, checkpoint=checkpoint, error=reason)
            return state
        except Exception:
            log.exception("release %s status report failed", release_id)
            return "report_failed"
    finally:
        if job_dir.exists():
            shutil.rmtree(job_dir)


def main() -> None:
    try:
        validate_config()
    except DeliveryError as exc:
        log.error("worker configuration invalid: %s", exc)
        sys.exit(1)
    log.info("DMB worker started; api=%s worker=%s", API_BASE_URL, WORKER_ID)
    while True:
        circuit_state = read_circuit_state()
        if circuit_state["open"]:
            log.error("DMB circuit open; manual review required")
            time.sleep(max(POLL_INTERVAL, 60))
            continue
        try:
            for release in get_pending("create"):
                release_id = _validated_release_id(release.get("id"))
                outcome = process_release(release)
                if record_delivery_outcome(release_id, outcome):
                    log.error("DMB circuit opened after release %s", release_id)
        except Exception:
            log.exception("poll loop failed")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
