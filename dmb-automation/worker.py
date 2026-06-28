"""
DMB automation worker (mini-app ↔ DMB bridge).

Polls the mini-app's internal API for pending releases, downloads the audio + cover
from MinIO, writes them into the local SQLite `album_metadata` table that the Robot
Framework suite reads, runs the DMB album-creation automation, and reports the result
back to the mini-app.

Transport:  internal HTTP API (bearer token) — see backend/routers/internal.py
Files:      pulled directly from MinIO/S3 via boto3 using the stored object keys
Runtime:    designed to run in the Docker image (Firefox + geckodriver + Xvfb)
"""

import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import boto3
import requests

# ── Configuration (from environment) ────────────────────────────────────────────
API_BASE_URL   = os.getenv("API_BASE_URL", "http://backend:8000").rstrip("/")
SECRET         = os.getenv("SELENIUM_SECRET_KEY", "")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY  = os.getenv("S3_ACCESS_KEY", "admin")
S3_SECRET_KEY  = os.getenv("S3_SECRET_KEY", "password123")
S3_BUCKET      = os.getenv("S3_BUCKET", "nitro-bot")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", "30"))
DRY_RUN        = os.getenv("DRY_RUN", "false").lower() == "true"
DMB_USERNAME   = os.getenv("DMB_USERNAME", "")
DMB_PASSWORD   = os.getenv("DMB_PASSWORD", "")

BASE_DIR     = Path(__file__).resolve().parent
DB_PATH      = BASE_DIR / "resources" / "database" / "dmb_database.db"
DOWNLOAD_DIR = BASE_DIR / "downloads"
RESULTS_DIR  = BASE_DIR / "results"
ROBOT_SUITE  = "automation/create_album.robot"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
log = logging.getLogger("dmb-automation")

_s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="us-east-1",
)

_http = requests.Session()
_http.headers.update({"Authorization": f"Bearer {SECRET}"})


# ── API helpers ──────────────────────────────────────────────────────────────────
def get_pending() -> list[dict]:
    resp = _http.get(f"{API_BASE_URL}/internal/releases/pending", timeout=30)
    resp.raise_for_status()
    return resp.json()


def set_status(release_id: int, status: str) -> None:
    resp = _http.post(
        f"{API_BASE_URL}/internal/releases/{release_id}/status",
        data={"status": status},
        timeout=30,
    )
    resp.raise_for_status()


# ── File + DB helpers ──────────────────────────────────────────────────────────────
def download(key: str, dest_dir: Path, label: str) -> Path:
    """Download an S3/MinIO object to a local file, preserving its extension."""
    ext = os.path.splitext(key)[1]
    local = dest_dir / f"{label}{ext}"
    _s3.download_file(S3_BUCKET, key, str(local))
    log.info("downloaded %s -> %s", key, local)
    return local


def format_release_date(value: str) -> str:
    """
    The mini-app sends Gregorian YYYY-MM-DD, which the DMB date field currently accepts.
    If the live DMB form turns out to require DD.MM.YYYY (German platform), reformat here.
    See plan Part G.
    """
    return value


def write_sqlite(rel: dict, cover_path: Path, music_path: Path) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS album_metadata (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                title            TEXT NOT NULL,
                artist_name      TEXT NOT NULL,
                legal_name       TEXT NOT NULL,
                cover_image_path TEXT NOT NULL,
                music_file_path  TEXT NOT NULL,
                release_date     TEXT NOT NULL,
                genre            TEXT
            )
            """
        )
        cur.execute("DELETE FROM album_metadata")
        cur.execute(
            """
            INSERT INTO album_metadata
                (title, artist_name, legal_name, cover_image_path, music_file_path, release_date, genre)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rel["song_name"],
                rel["artist_name"],
                rel["legal_name"],
                str(cover_path),
                str(music_path),
                format_release_date(rel["release_date"]),
                rel.get("genre") or "",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("wrote album_metadata row for release %s", rel["id"])


def run_robot(release_id: int) -> bool:
    """Run the Robot suite under a virtual display. Returns True on success (exit 0)."""
    outdir = RESULTS_DIR / str(release_id)
    env = {**os.environ, "DMB_USERNAME": DMB_USERNAME, "DMB_PASSWORD": DMB_PASSWORD}
    cmd = ["xvfb-run", "-a", "robot", "--outputdir", str(outdir), ROBOT_SUITE]
    log.info("running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
    return proc.returncode == 0


# ── Per-release processing ─────────────────────────────────────────────────────────
def process(rel: dict) -> None:
    rid = rel["id"]
    log.info("processing release %s: %r by %r", rid, rel.get("song_name"), rel.get("artist_name"))
    set_status(rid, "processing")

    job_dir = DOWNLOAD_DIR / str(rid)
    if job_dir.exists():
        shutil.rmtree(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        cover = download(rel["cover_url"], job_dir, "cover")
        music = download(rel["track_url"], job_dir, "track")
        write_sqlite(rel, cover, music)

        if DRY_RUN:
            log.info("DRY_RUN=1 — wrote SQLite + files, skipping Robot run for release %s", rid)
            return

        ok = run_robot(rid)
        set_status(rid, "completed" if ok else "failed")
        log.info("release %s -> %s", rid, "completed" if ok else "failed")
    except Exception:
        log.exception("release %s failed", rid)
        try:
            set_status(rid, "failed")
        except Exception:
            log.exception("could not report failed status for release %s", rid)


# ── Main loop ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not SECRET:
        log.error("SELENIUM_SECRET_KEY is not set; refusing to start.")
        sys.exit(1)
    if not DRY_RUN and (not DMB_USERNAME or not DMB_PASSWORD):
        log.error("DMB_USERNAME / DMB_PASSWORD not set; refusing to start (set DRY_RUN=true to test without them).")
        sys.exit(1)

    log.info(
        "DMB automation worker started. api=%s bucket=%s poll=%ss dry_run=%s",
        API_BASE_URL, S3_BUCKET, POLL_INTERVAL, DRY_RUN,
    )
    # NOTE (plan follow-up): a release marked "processing" that crashes mid-run stays
    # "processing" and won't be re-picked. A future sweep could reset stale rows.
    while True:
        try:
            pending = get_pending()
            if pending:
                pending.sort(key=lambda r: r.get("created_at") or "")  # oldest first
                log.info("found %d pending release(s)", len(pending))
                for rel in pending:
                    process(rel)
        except Exception:
            log.exception("poll loop error")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
