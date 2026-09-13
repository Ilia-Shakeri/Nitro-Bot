import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("dmb_worker", ROOT / "worker.py")
worker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(worker)

LIB_SPEC = importlib.util.spec_from_file_location(
    "dmb_job_library",
    ROOT / "libraries" / "dmb_job.py",
)
dmb_job_module = importlib.util.module_from_spec(LIB_SPEC)
assert LIB_SPEC.loader is not None
LIB_SPEC.loader.exec_module(dmb_job_module)


def sample_release() -> dict:
    return {
        "id": 42,
        "user_id": 100,
        "song_name": "Safe Song",
        "artist_name": "Main feat. Guest",
        "artists": [
            {"name": "Main", "role": "primary"},
            {"name": "Guest", "role": "featured"},
        ],
        "producers": '["Producer"]',
        "legal_name": "Legal Name",
        "legal_names": ["Legal Name"],
        "release_date": "2026-12-01",
        "is_rerelease": True,
        "original_release_date": "2020-01-01",
        "genre": "Pop",
        "sub_genre": "Synth Pop",
        "track_url": "releases/100/42/track.wav",
        "cover_url": "releases/100/42/cover.png",
        "mapping_spotify": "https://open.spotify.com/artist/main",
        "mapping_apple": None,
        "profile_email": None,
        "requires_new_profile": False,
        "artist_mappings": [
            {
                "artist_name": "Main",
                "requires_new_profile": False,
                "spotify_url": "https://open.spotify.com/artist/main",
                "apple_music_url": None,
                "profile_email": None,
            },
            {
                "artist_name": "Guest",
                "requires_new_profile": True,
                "spotify_url": None,
                "apple_music_url": None,
                "profile_email": "guest@example.com",
            },
        ],
        "policy_accepted_at": "2026-09-13T00:00:00",
        "policy_version": "1.0",
        "is_edit": False,
        "source_release_id": None,
        "source_dmb_release_id": None,
        "copyright_requested": True,
        "explicit_content": True,
        "charged_cost": 10,
        "status": "processing",
        "dmb_attempts": 1,
        "created_at": "2026-09-13T00:00:00",
    }


def test_job_payload_carries_full_release_contract(tmp_path):
    release = sample_release()
    payload = worker.build_job_payload(
        release,
        tmp_path / "cover.png",
        tmp_path / "track.wav",
    )
    assert payload["schema_version"] == 1
    assert payload["mode"] == "create"
    for field in (
        "artists",
        "producers",
        "legal_names",
        "is_rerelease",
        "original_release_date",
        "genre",
        "sub_genre",
        "artist_mappings",
        "copyright_requested",
        "explicit_content",
    ):
        assert payload[field] == release[field]


def test_edit_contract_requires_delivered_source():
    release = sample_release()
    release["is_edit"] = True
    with pytest.raises(worker.DeliveryError, match="edit_source_evidence_missing"):
        worker.validate_release_contract(release)


def test_claimed_bad_contract_is_reported_for_retry(monkeypatch):
    release = sample_release()
    release.pop("song_name")
    report = MagicMock()
    monkeypatch.setattr(worker, "set_status", report)

    worker.process_release(release)

    report.assert_called_once()
    assert report.call_args.args == (42, "retry")
    assert "release_contract_incomplete" in report.call_args.kwargs["error"]


def test_result_requires_submit_marker_and_real_codes(tmp_path, monkeypatch):
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(worker, "RESULTS_DIR", tmp_path)
    output_dir = tmp_path / "42"
    output_dir.mkdir()
    screenshot = output_dir / "submitted.png"
    screenshot.write_bytes(b"evidence")
    result_path.write_text(
        json.dumps(
            {
                "submitted": True,
                "release_id": 42,
                "dmb_release_id": "album-42",
                "ean_upc": "1234567890123",
                "isrcs": ["USABC2600001"],
                "current_url": "https://dmb.kontornewmedia.com/music/albums/album-42",
                "screenshot_path": str(screenshot),
            }
        ),
        encoding="utf-8",
    )
    result = worker.load_result(result_path, 42)
    assert result["evidence_path"] == "results/42"
    result_path.write_text("{}", encoding="utf-8")
    with pytest.raises(worker.DeliveryError, match="dmb_result_evidence_invalid"):
        worker.load_result(result_path, 42)


def test_job_library_writes_atomic_verified_result(tmp_path):
    library = dmb_job_module.DmbJob()
    result_path = tmp_path / "result.json"
    library.write_dmb_result(
        str(result_path),
        42,
        "album-42",
        "1234567890123",
        "usabc2600001",
        "https://dmb.kontornewmedia.com/music/albums/album-42",
        "results/42/submitted.png",
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["submitted"] is True
    assert result["isrcs"] == ["USABC2600001"]
    assert not result_path.with_suffix(".json.tmp").exists()


def test_job_library_rejects_result_id_not_in_url(tmp_path):
    library = dmb_job_module.DmbJob()
    with pytest.raises(ValueError, match="dmb_result_release_id_mismatch"):
        library.write_dmb_result(
            str(tmp_path / "result.json"),
            42,
            "album-99",
            "1234567890123",
            "USABC2600001",
            "https://dmb.kontornewmedia.com/music/albums/album-42",
            "results/42/submitted.png",
        )


def test_submit_checkpoint_is_atomic(tmp_path):
    library = dmb_job_module.DmbJob()
    checkpoint = tmp_path / "submit-started.json"
    library.write_submit_checkpoint(str(checkpoint), 42)
    stored = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert stored["release_id"] == 42
    assert stored["started_at"].endswith("+00:00")
    assert not checkpoint.with_suffix(".json.tmp").exists()


def test_release_id_is_extracted_from_query_or_path():
    library = dmb_job_module.DmbJob()
    assert library.extract_dmb_release_id("https://dmb.kontornewmedia.com/music/album/abc-42") == "abc-42"
    assert library.extract_dmb_release_id("https://dmb.kontornewmedia.com/music?albumId=77") == "77"
    with pytest.raises(ValueError, match="dmb_release_id_not_found"):
        library.extract_dmb_release_id("https://dmb.kontornewmedia.com/music/success")
