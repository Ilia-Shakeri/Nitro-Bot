"""Publish one already-saved DMB album after a verified create checkpoint."""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RECOVERY_SUITE = BASE_DIR / "automation" / "recover_publish.robot"
_DMB_ID_RE = re.compile(r"^(?=[A-Za-z0-9._:-]{1,128}$)(?=.*\d)[A-Za-z0-9._:-]+$")
_EAN_RE = re.compile(r"^\d{8,14}$")
_ISRC_RE = re.compile(r"^[A-Z0-9-]{8,20}$")


class RecoveryError(RuntimeError):
    pass


def positive_release_id(value: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", value.strip()):
        raise RecoveryError("dmb_recovery_release_id_invalid")
    return int(value)


def load_checkpoint(path: Path, release_id: int) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        started_at = datetime.fromisoformat(str(payload["started_at"]))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise RecoveryError("dmb_recovery_checkpoint_invalid") from None
    isrcs = payload.get("isrcs")
    if (
        payload.get("release_id") != release_id
        or not _EAN_RE.fullmatch(str(payload.get("ean_upc", "")))
        or not isinstance(isrcs, list)
        or len(isrcs) != 1
        or not isinstance(isrcs[0], str)
        or not _ISRC_RE.fullmatch(isrcs[0])
        or started_at.tzinfo is None
    ):
        raise RecoveryError("dmb_recovery_checkpoint_invalid")
    return payload


def validate_result(path: Path, release_id: int, dmb_id: str, checkpoint: dict) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RecoveryError("dmb_recovery_result_invalid") from None
    screenshot = Path(str(payload.get("screenshot_path", ""))).resolve()
    parsed_url = urlparse(str(payload.get("current_url", "")))
    if (
        payload.get("submitted") is not True
        or payload.get("release_id") != release_id
        or payload.get("dmb_release_id") != dmb_id
        or payload.get("ean_upc") != checkpoint["ean_upc"]
        or payload.get("isrcs") != checkpoint["isrcs"]
        or parsed_url.scheme != "https"
        or parsed_url.hostname != os.getenv("DMB_ALLOWED_HOST", "dmb.kontornewmedia.com")
        or parsed_url.path.rstrip("/") != f"/page/album/{dmb_id}"
        or not screenshot.is_file()
        or RESULTS_DIR.resolve() not in screenshot.parents
    ):
        raise RecoveryError("dmb_recovery_result_invalid")
    return payload


def main() -> int:
    try:
        release_id = positive_release_id(os.getenv("DMB_RECOVERY_RELEASE_ID", ""))
        dmb_id = os.getenv("DMB_RECOVERY_DMB_ID", "").strip()
        if not _DMB_ID_RE.fullmatch(dmb_id):
            raise RecoveryError("dmb_recovery_dmb_id_invalid")
        checkpoint_path = RESULTS_DIR / str(release_id) / "submit-started.json"
        checkpoint = load_checkpoint(checkpoint_path, release_id)
        output_dir = RESULTS_DIR / str(release_id) / "recovery"
        result_path = output_dir / "result.json"
        if result_path.exists():
            raise RecoveryError("dmb_recovery_result_exists")
        output_dir.mkdir(parents=True, exist_ok=True)
        env = {
            **os.environ,
            "DMB_RECOVERY_RELEASE_ID": str(release_id),
            "DMB_RECOVERY_DMB_ID": dmb_id,
            "DMB_RECOVERY_EAN": checkpoint["ean_upc"],
            "DMB_RECOVERY_ISRC": checkpoint["isrcs"][0],
            "DMB_RESULT_FILE": str(result_path),
            "DMB_PUBLISH_ENABLED": "true",
        }
        process = subprocess.run(
            ["robot", "--outputdir", str(output_dir), str(RECOVERY_SUITE)],
            cwd=str(BASE_DIR),
            env=env,
            check=False,
        )
        if process.returncode != 0:
            raise RecoveryError(f"dmb_recovery_robot_exit_{process.returncode}")
        validate_result(result_path, release_id, dmb_id, checkpoint)
        print(f"recovery_ok release_id={release_id} dmb_release_id={dmb_id}")
        return 0
    except Exception as exc:
        print(f"recovery_failed {type(exc).__name__}:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
