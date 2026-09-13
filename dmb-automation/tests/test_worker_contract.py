import importlib.util
import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

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
                "dmb_has_account": True,
                "spotify_url": "https://open.spotify.com/artist/main",
                "apple_music_url": None,
                "profile_email": None,
            },
            {
                "artist_name": "Guest",
                "requires_new_profile": True,
                "dmb_has_account": False,
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
    assert payload["schema_version"] == 2
    assert payload["mode"] == "create"
    assert payload["dmb_genre"] == "Pop"
    assert payload["label"] == "Mitrxv"
    assert payload["metadata_language"] == "English"
    assert payload["expiration_date"] == "2099-12-31"
    assert payload["price_code"] == "MA"
    assert payload["itunes_price_code"] == "14"
    assert payload["c_line_year"] == "2020"
    assert payload["p_line_year"] == str(date.today().year)
    assert payload["contributors"] == [
        {"name": "Main", "has_account": True, "role": "Performer"},
        {"name": "Guest", "has_account": False, "role": "Performer"},
    ]
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


def test_every_canonical_genre_builds_exact_dmb_text():
    genre_tree = json.loads((ROOT.parent / "shared" / "release-genres.json").read_text(encoding="utf-8"))
    for genre, sub_genres in genre_tree.items():
        assert worker.dmb_genre_text(genre, None) == genre
        for sub_genre in sub_genres:
            assert worker.dmb_genre_text(genre, sub_genre) == f"{sub_genre} [{genre}]"


def test_contributor_account_is_not_inferred_from_streaming_profile():
    release = sample_release()
    release["artist_mappings"][0]["requires_new_profile"] = False
    release["artist_mappings"][0]["dmb_has_account"] = False
    payload = worker.build_job_payload(release, Path("cover.jpg"), Path("track.wav"))
    assert payload["contributors"][0]["has_account"] is False


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

    outcome = worker.process_release(release)

    assert outcome == "retry"
    report.assert_called_once()
    assert report.call_args.args == (42, "retry")
    assert "release_contract_incomplete" in report.call_args.kwargs["error"]


def test_result_requires_submit_marker_and_real_codes(tmp_path, monkeypatch):
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(worker, "RESULTS_DIR", tmp_path)
    output_dir = tmp_path / "42"
    output_dir.mkdir()
    screenshot = output_dir / "submitted.png"
    Image.new("RGB", (100, 100), "white").save(screenshot)
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


def test_job_library_formats_iso_dates_for_live_dmb_form():
    library = dmb_job_module.DmbJob()
    assert library.format_dmb_date("2026-12-01") == "01.12.2026"
    with pytest.raises(ValueError, match="dmb_job_date_invalid"):
        library.format_dmb_date("01.12.2026")


def test_job_loader_rejects_media_outside_job_directory(tmp_path):
    payload = worker.build_job_payload(
        sample_release(),
        tmp_path / "cover.jpg",
        tmp_path / "track.wav",
    )
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    job_file = job_dir / "job.json"
    job_file.write_text(json.dumps(payload), encoding="utf-8")
    library = dmb_job_module.DmbJob()
    with pytest.raises(ValueError, match="dmb_job_media_path_invalid"):
        library.load_dmb_job(str(job_file))


def test_job_loader_accepts_worker_media_contract(tmp_path):
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    cover = job_dir / "cover.jpg"
    track = job_dir / "track.wav"
    payload = worker.build_job_payload(sample_release(), cover, track)
    job_file = job_dir / "job.json"
    job_file.write_text(json.dumps(payload), encoding="utf-8")
    assert dmb_job_module.DmbJob().load_dmb_job(str(job_file))["release_id"] == 42


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


def test_popular_urban_genre_keeps_exact_dmb_value(tmp_path):
    release = sample_release()
    release["genre"] = "HipHop / Rap [Urban]"
    release["sub_genre"] = "Trap"
    payload = worker.build_job_payload(
        release,
        tmp_path / "cover.jpg",
        tmp_path / "track.wav",
    )
    assert payload["dmb_genre"] == "HipHop / Rap [Urban]"


def test_unknown_dmb_subgenre_fails_closed(tmp_path):
    release = sample_release()
    release["sub_genre"] = "Made Up"
    with pytest.raises(ValueError, match="dmb_sub_genre_not_mapped"):
        worker.build_job_payload(
            release,
            tmp_path / "cover.jpg",
            tmp_path / "track.wav",
        )


def test_every_mini_app_genre_has_a_dmb_mapping():
    genre_tree = json.loads(
        (ROOT.parent / "shared" / "release-genres.json").read_text(encoding="utf-8")
    )
    for genre, sub_genres in genre_tree.items():
        assert worker.dmb_genre_text(genre, None)
        for sub_genre in sub_genres:
            assert worker.dmb_genre_text(genre, sub_genre)


def test_cover_is_exact_3000_square_jpeg(tmp_path):
    source = tmp_path / "source.png"
    destination = tmp_path / "cover.jpg"
    Image.new("RGBA", (3100, 3200), (255, 0, 0, 128)).save(source)

    worker.prepare_cover_for_dmb(source, destination)

    with Image.open(destination) as cover:
        assert cover.format == "JPEG"
        assert cover.size == (3000, 3000)
        assert cover.mode == "RGB"


def test_non_wav_track_is_rejected(tmp_path):
    track = tmp_path / "track.wav"
    track.write_bytes(b"not really a wave file")
    with pytest.raises(worker.DeliveryError, match="dmb_track_must_be_wav"):
        worker.validate_track_for_dmb(track)


def test_robot_flow_contains_attachment_steps():
    suite = (ROOT / "automation" / "create_album.robot").read_text(encoding="utf-8")
    page = (ROOT / "resources" / "pages" / "album_page.robot").read_text(
        encoding="utf-8"
    )
    locators = (ROOT / "resources" / "locators" / "album_locators.robot").read_text(
        encoding="utf-8"
    )
    for step in (
        "Set Label",
        "Open Add Tracks",
        "Select Worldwide And Next",
        "Select All Platforms And Next",
        "Verify Review Data",
        "Apply Contributors To Tracks",
    ):
        assert step in suite or step in page
    assert "Save & View Audio Product" in locators
    assert "    Sleep" not in page


def test_live_verified_navigation_and_field_locators_are_pinned():
    login_locators = (
        ROOT / "resources" / "locators" / "login_locators.robot"
    ).read_text(encoding="utf-8")
    album_page = (ROOT / "resources" / "pages" / "album_page.robot").read_text(
        encoding="utf-8"
    )
    assert "normalize-space()='Audio'" in login_locators
    assert "normalize-space()='Create audio product'" in login_locators
    assert "//iframe[contains(@src, 'album.create')]" in login_locators
    assert "Select From List By Label    ${LABEL_SELECT}" in album_page
    assert album_page.count("Replace String    ${AJAX_EXACT_OPTION}") == 3


def test_circuit_opens_after_bounded_failures_and_clears_on_success(
    tmp_path, monkeypatch
):
    state_path = tmp_path / "dmb-circuit.json"
    monkeypatch.setattr(worker, "CIRCUIT_STATE_PATH", state_path)
    monkeypatch.setattr(worker, "CIRCUIT_FAILURE_LIMIT", 3)

    assert worker.record_delivery_outcome(1, "retry") is False
    assert worker.record_delivery_outcome(2, "retry") is False
    assert worker.record_delivery_outcome(3, "retry") is True
    assert worker.read_circuit_state()["open"] is True

    assert worker.record_delivery_outcome(4, "completed") is False
    assert not state_path.exists()


def test_uncertain_delivery_opens_circuit_immediately(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "CIRCUIT_STATE_PATH", tmp_path / "dmb-circuit.json")
    monkeypatch.setattr(worker, "CIRCUIT_FAILURE_LIMIT", 3)
    assert worker.record_delivery_outcome(42, "uncertain") is True
    assert worker.read_circuit_state()["outcome"] == "uncertain"


def test_invalid_circuit_state_fails_closed(tmp_path, monkeypatch):
    state_path = tmp_path / "dmb-circuit.json"
    state_path.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(worker, "CIRCUIT_STATE_PATH", state_path)
    assert worker.read_circuit_state()["open"] is True


def test_successful_release_reports_verified_completion(tmp_path, monkeypatch):
    release = sample_release()
    monkeypatch.setattr(worker, "DOWNLOAD_DIR", tmp_path / "downloads")
    monkeypatch.setattr(worker, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(worker, "download", lambda key, path: path)
    monkeypatch.setattr(worker, "prepare_cover_for_dmb", lambda source, path: path)
    monkeypatch.setattr(worker, "validate_track_for_dmb", lambda path: path)
    monkeypatch.setattr(
        worker,
        "run_robot",
        lambda *args: {
            "dmb_release_id": "album-42",
            "ean_upc": "1234567890123",
            "isrcs": ["USABC2600001"],
            "evidence_path": "results/42",
        },
    )
    report = MagicMock()
    monkeypatch.setattr(worker, "set_status", report)

    assert worker.process_release(release) == "completed"
    report.assert_called_once()
    assert report.call_args.args == (42, "completed")
    assert report.call_args.kwargs["result"]["dmb_release_id"] == "album-42"


def test_failure_after_save_checkpoint_requires_manual_verification(
    tmp_path, monkeypatch
):
    release = sample_release()
    monkeypatch.setattr(worker, "DOWNLOAD_DIR", tmp_path / "downloads")
    monkeypatch.setattr(worker, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(worker, "download", lambda key, path: path)
    monkeypatch.setattr(worker, "prepare_cover_for_dmb", lambda source, path: path)
    monkeypatch.setattr(worker, "validate_track_for_dmb", lambda path: path)

    def fail_after_checkpoint(release_id, job_file, result_file, checkpoint_file):
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text("{}", encoding="utf-8")
        raise worker.DeliveryError("browser_lost_after_save")

    monkeypatch.setattr(worker, "run_robot", fail_after_checkpoint)
    report = MagicMock()
    monkeypatch.setattr(worker, "set_status", report)

    assert worker.process_release(release) == "uncertain"
    assert report.call_args.args == (42, "uncertain")
    assert "browser_lost_after_save" in report.call_args.kwargs["error"]
