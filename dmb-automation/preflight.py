"""Run one allowlisted create release to the DMB review page without saving it."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests

from worker import (
    API_BASE_URL,
    BASE_DIR,
    CREATE_SUITE,
    DMB_BROWSER_MODE,
    DMB_PASSWORD,
    DMB_USERNAME,
    DOWNLOAD_DIR,
    RESULTS_DIR,
    SECRET,
    build_job_payload,
    download,
    prepare_cover_for_dmb,
    validate_release_contract,
    validate_track_for_dmb,
    write_json_atomic,
)


def _release_id() -> int:
    try:
        value = int(os.environ["DMB_PREFLIGHT_RELEASE_ID"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("dmb_preflight_release_id_invalid") from None
    if value <= 0:
        raise RuntimeError("dmb_preflight_release_id_invalid")
    return value


def _fetch_release(release_id: int) -> dict:
    if not SECRET:
        raise RuntimeError("dmb_worker_secret_missing")
    response = requests.get(
        f"{API_BASE_URL}/internal/releases/{release_id}/preflight",
        headers={
            "Authorization": f"Bearer {SECRET}",
            "X-DMB-Worker-ID": "dmb-preflight",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("id") != release_id:
        raise RuntimeError("dmb_preflight_response_invalid")
    if payload.get("is_edit"):
        raise RuntimeError("dmb_preflight_create_only")
    validate_release_contract(payload)
    return payload


def run() -> Path:
    release_id = _release_id()
    release = _fetch_release(release_id)
    job_dir = DOWNLOAD_DIR / f"preflight-{release_id}"
    output_dir = RESULTS_DIR / f"preflight-{release_id}"
    result_file = output_dir / "preflight.json"
    if job_dir.exists():
        shutil.rmtree(job_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    job_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    try:
        source_cover = download(release["cover_url"], job_dir / "source-cover")
        cover = prepare_cover_for_dmb(source_cover, job_dir / "cover.jpg")
        track = validate_track_for_dmb(
            download(release["track_url"], job_dir / "track.wav")
        )
        job_file = job_dir / "job.json"
        write_json_atomic(job_file, build_job_payload(release, cover, track))
        env = {
            **os.environ,
            "DMB_USERNAME": DMB_USERNAME,
            "DMB_PASSWORD": DMB_PASSWORD,
            "DMB_JOB_FILE": str(job_file),
            "DMB_PREFLIGHT_ENABLED": "true",
            "DMB_PREFLIGHT_RESULT": str(result_file),
            "DMB_SUBMIT_ENABLED": "false",
            "DMB_BROWSER_MODE": DMB_BROWSER_MODE,
        }
        process = subprocess.run(
            ["robot", "--outputdir", str(output_dir), str(CREATE_SUITE)],
            cwd=str(BASE_DIR),
            env=env,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"dmb_preflight_robot_exit_{process.returncode}")
        result = json.loads(result_file.read_text(encoding="utf-8"))
        if result.get("submitted") is not False or result.get("release_id") != release_id:
            raise RuntimeError("dmb_preflight_result_invalid")
        return result_file
    finally:
        if job_dir.exists():
            shutil.rmtree(job_dir)


if __name__ == "__main__":
    try:
        evidence = run()
        print(f"preflight_ok evidence={evidence}")
    except Exception as exc:
        print(f"preflight_failed {type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
