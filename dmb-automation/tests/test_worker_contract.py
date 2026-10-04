import importlib.util
import json
import urllib.error
import urllib.request
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

RECOVERY_SPEC = importlib.util.spec_from_file_location(
    "dmb_recover_publish", ROOT / "recover_publish.py"
)
recover_publish = importlib.util.module_from_spec(RECOVERY_SPEC)
assert RECOVERY_SPEC.loader is not None
RECOVERY_SPEC.loader.exec_module(recover_publish)


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


def sample_edit_release() -> dict:
    release = sample_release()
    release.update(
        {
            "is_edit": True,
            "source_release_id": 7,
            "source_dmb_release_id": "2222756",
            "source_dmb_ean_upc": "4069977537588",
            "source_dmb_isrcs": ["USABC2600001"],
            "source_cover_url": "releases/100/7/cover.png",
        }
    )
    return release


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


def test_edit_job_keeps_exact_source_evidence(tmp_path):
    job_dir = tmp_path / "42"
    job_dir.mkdir()
    payload = worker.build_job_payload(
        sample_edit_release(),
        job_dir / "cover.jpg",
        job_dir / "track.wav",
    )
    job_file = job_dir / "job.json"
    job_file.write_text(json.dumps(payload), encoding="utf-8")

    job = dmb_job_module.DmbJob().load_dmb_job(str(job_file))

    assert job["mode"] == "edit"
    assert job["source_dmb_release_id"] == "2222756"
    assert job["source_dmb_ean_upc"] == "4069977537588"
    assert job["source_dmb_isrcs"] == ["USABC2600001"]


def test_edit_worker_needs_distinct_submit_gate(monkeypatch):
    monkeypatch.setattr(worker, "SECRET", "worker-secret")
    monkeypatch.setattr(worker, "S3_ACCESS_KEY", "access")
    monkeypatch.setattr(worker, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(worker, "DMB_USERNAME", "user")
    monkeypatch.setattr(worker, "DMB_PASSWORD", "pass")
    monkeypatch.setattr(worker, "DRY_RUN", False)
    monkeypatch.setattr(worker, "CREATE_ENABLED", False)
    monkeypatch.setattr(worker, "EDIT_ENABLED", True)
    monkeypatch.setattr(worker, "EDIT_SUBMIT_ENABLED", False)
    with pytest.raises(worker.DeliveryError, match="DMB_edit_submit_disabled"):
        worker.validate_config()


def test_worker_allows_safe_dry_run_standby(monkeypatch):
    monkeypatch.setattr(worker, "SECRET", "worker-secret")
    monkeypatch.setattr(worker, "S3_ACCESS_KEY", "access")
    monkeypatch.setattr(worker, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(worker, "DMB_USERNAME", "user")
    monkeypatch.setattr(worker, "DMB_PASSWORD", "pass")
    monkeypatch.setattr(worker, "DRY_RUN", True)
    monkeypatch.setattr(worker, "CREATE_ENABLED", False)
    monkeypatch.setattr(worker, "EDIT_ENABLED", False)

    worker.validate_config()
    health = worker.health_snapshot()
    assert health["standby"] is True
    assert health["delivery_enabled"] is False


def test_worker_rejects_dry_run_with_live_delivery_gate(monkeypatch):
    monkeypatch.setattr(worker, "SECRET", "worker-secret")
    monkeypatch.setattr(worker, "S3_ACCESS_KEY", "access")
    monkeypatch.setattr(worker, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(worker, "DMB_USERNAME", "user")
    monkeypatch.setattr(worker, "DMB_PASSWORD", "pass")
    monkeypatch.setattr(worker, "DRY_RUN", True)
    monkeypatch.setattr(worker, "CREATE_ENABLED", True)
    monkeypatch.setattr(worker, "EDIT_ENABLED", False)

    with pytest.raises(worker.DeliveryError, match="DRY_RUN_cannot_claim_live_jobs"):
        worker.validate_config()


def test_worker_rejects_unknown_browser_mode(monkeypatch):
    monkeypatch.setattr(worker, "SECRET", "worker-secret")
    monkeypatch.setattr(worker, "S3_ACCESS_KEY", "access")
    monkeypatch.setattr(worker, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(worker, "DMB_USERNAME", "user")
    monkeypatch.setattr(worker, "DMB_PASSWORD", "pass")
    monkeypatch.setattr(worker, "DRY_RUN", False)
    monkeypatch.setattr(worker, "CREATE_ENABLED", True)
    monkeypatch.setattr(worker, "EDIT_ENABLED", False)
    monkeypatch.setattr(worker, "DMB_BROWSER_MODE", "unknown")
    with pytest.raises(worker.DeliveryError, match="DMB_browser_mode_invalid"):
        worker.validate_config()


def test_worker_rejects_invalid_target_release(monkeypatch):
    monkeypatch.setattr(worker, "SECRET", "worker-secret")
    monkeypatch.setattr(worker, "S3_ACCESS_KEY", "access")
    monkeypatch.setattr(worker, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(worker, "DMB_USERNAME", "user")
    monkeypatch.setattr(worker, "DMB_PASSWORD", "pass")
    monkeypatch.setattr(worker, "DRY_RUN", False)
    monkeypatch.setattr(worker, "CREATE_ENABLED", True)
    monkeypatch.setattr(worker, "EDIT_ENABLED", False)
    monkeypatch.setattr(worker, "DMB_BROWSER_MODE", "headless")
    monkeypatch.setattr(worker, "TARGET_RELEASE_ID_RAW", "bad")
    monkeypatch.setattr(worker, "TARGET_RELEASE_ID", None)
    with pytest.raises(worker.DeliveryError, match="DMB_target_release_id_invalid"):
        worker.validate_config()


def test_worker_requests_only_target_release(monkeypatch):
    response = MagicMock()
    response.json.return_value = []
    monkeypatch.setattr(worker._http, "get", MagicMock(return_value=response))
    monkeypatch.setattr(worker, "TARGET_RELEASE_ID", 11)

    assert worker.get_pending("create") == []
    worker._http.get.assert_called_once_with(
        f"{worker.API_BASE_URL}/internal/releases/pending",
        params={"mode": "create", "release_id": 11},
        timeout=30,
    )


def test_worker_health_requires_poll_and_closed_circuit(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "CIRCUIT_STATE_PATH", tmp_path / "circuit.json")
    worker.update_health(poll_ok=False, last_error="starting")
    assert worker.health_snapshot()["ready"] is False

    worker.update_health(poll_ok=True, last_error=None)
    assert worker.health_snapshot()["ready"] is True

    worker.write_json_atomic(
        worker.CIRCUIT_STATE_PATH,
        {"open": True, "failures": 1},
    )
    assert worker.health_snapshot()["ready"] is False


def test_worker_health_http_endpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "CIRCUIT_STATE_PATH", tmp_path / "circuit.json")
    monkeypatch.setattr(worker, "HEALTH_HOST", "127.0.0.1")
    monkeypatch.setattr(worker, "HEALTH_PORT", 0)
    worker.update_health(poll_ok=False, last_error="starting")
    server = worker.start_health_server()
    port = server.server_address[1]
    try:
        live = urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health/live",
            timeout=2,
        )
        assert live.status == 200
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health/ready",
                timeout=2,
            )
        assert exc.value.code == 503

        worker.update_health(poll_ok=True, last_error=None)
        ready = urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health/ready",
            timeout=2,
        )
        assert ready.status == 200
    finally:
        server.shutdown()
        server.server_close()


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
    library.write_submit_checkpoint(
        str(checkpoint),
        42,
        "1234567890123",
        "USABC2600001",
        "Safe Title",
    )
    stored = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert stored["release_id"] == 42
    assert stored["ean_upc"] == "1234567890123"
    assert stored["isrcs"] == ["USABC2600001"]
    assert stored["title"] == "Safe Title"
    assert stored["started_at"].endswith("+00:00")
    assert not checkpoint.with_suffix(".json.tmp").exists()


def test_submit_checkpoint_loads_with_stable_fingerprint(tmp_path):
    library = dmb_job_module.DmbJob()
    checkpoint = tmp_path / "submit-started.json"
    library.write_submit_checkpoint(
        str(checkpoint),
        42,
        "1234567890123",
        "USABC2600001",
        "Safe Title",
    )
    loaded = worker.load_submit_checkpoint(checkpoint, 42, "Safe Title")
    assert loaded["submission_fingerprint"] == worker.submission_fingerprint(
        42,
        "Safe Title",
        "1234567890123",
        ["USABC2600001"],
    )


def test_submit_checkpoint_rejects_wrong_release_or_title(tmp_path):
    library = dmb_job_module.DmbJob()
    checkpoint = tmp_path / "submit-started.json"
    library.write_submit_checkpoint(
        str(checkpoint),
        42,
        "1234567890123",
        "USABC2600001",
        "Safe Title",
    )
    with pytest.raises(worker.DeliveryError, match="dmb_submit_checkpoint_invalid"):
        worker.load_submit_checkpoint(checkpoint, 43, "Safe Title")
    with pytest.raises(worker.DeliveryError, match="dmb_submit_checkpoint_invalid"):
        worker.load_submit_checkpoint(checkpoint, 42, "Other Title")


def test_result_must_match_pre_submit_checkpoint():
    result = {
        "ean_upc": "1234567890123",
        "isrcs": ["USABC2600001"],
    }
    checkpoint = {
        **result,
        "submission_fingerprint": "a" * 64,
    }
    assert worker.bind_result_to_checkpoint(result, checkpoint)[
        "submission_fingerprint"
    ] == "a" * 64
    with pytest.raises(worker.DeliveryError, match="dmb_result_checkpoint_mismatch"):
        worker.bind_result_to_checkpoint(
            {**result, "ean_upc": "1234567890124"},
            checkpoint,
        )


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
    ):
        assert step in suite or step in page
    assert "Apply Contributors To Tracks" not in suite
    assert "contributors2tracks" not in locators
    assert "Save & View Audio Product" in locators
    assert "    Sleep" not in page


def test_runtime_results_are_not_copied_into_images():
    dockerignore = (ROOT.parent / ".dockerignore").read_text(encoding="utf-8")
    assert "**/results" in dockerignore.splitlines()


def test_edit_flow_targets_source_and_has_two_submit_gates():
    suite = (ROOT / "automation" / "edit_album.robot").read_text(encoding="utf-8")
    page = (ROOT / "resources" / "pages" / "edit_album_page.robot").read_text(
        encoding="utf-8"
    )
    locators = (
        ROOT / "resources" / "locators" / "edit_album_locators.robot"
    ).read_text(encoding="utf-8")
    assert "${JOB}[source_dmb_release_id]" in suite
    assert "Write Submit Checkpoint" in suite
    assert "DMB_EDIT_SUBMIT_ENABLED" in page
    assert '"action":"save"' in locators
    assert '"action":"publish"' in locators
    assert "album.create" not in suite
    assert "    Sleep" not in page


def test_live_verified_navigation_and_field_locators_are_pinned():
    login_locators = (
        ROOT / "resources" / "locators" / "login_locators.robot"
    ).read_text(encoding="utf-8")
    login_page = (ROOT / "resources" / "pages" / "login_page.robot").read_text(
        encoding="utf-8"
    )
    locators = (ROOT / "resources" / "locators" / "album_locators.robot").read_text(
        encoding="utf-8"
    )
    album_page = (ROOT / "resources" / "pages" / "album_page.robot").read_text(
        encoding="utf-8"
    )
    create_suite = (ROOT / "automation" / "create_album.robot").read_text(
        encoding="utf-8"
    )
    edit_suite = (ROOT / "automation" / "edit_album.robot").read_text(
        encoding="utf-8"
    )
    assert "normalize-space()='Audio'" in login_locators
    assert "normalize-space()='Create audio product'" in login_locators
    assert "//iframe[contains(@src, 'album.create')]" in login_locators
    assert "not(self::option) and normalize-space()='(Maxi-) Single'" in locators
    assert "SeleniumLibrary.Input Password    ${PASSWORD_FIELD}" in login_page
    assert "Input Text    ${PASSWORD_FIELD}" not in login_page
    for suite in (create_suite, edit_suite):
        assert "Input DMB Password    ${password}" in suite
        assert "Input Password    ${password}" not in suite
        assert "Wait Until Page Contains Element    ${MUSIC_MENU}" in suite
        assert "Wait Until Element Is Visible    ${MUSIC_MENU}" not in suite
    assert "ARGUMENTS    ${music_menu}" in album_page
    assert "Execute Javascript    arguments[0].click();" in album_page
    assert "ARGUMENTS    ${create_link}" in album_page
    assert "${next_button}=    Get WebElement    ${NEXT_BUTTON}" in album_page
    assert "ARGUMENTS    ${next_button}" in album_page
    assert "Scroll Element Into View    ${NEXT_BUTTON}" not in album_page
    assert "Cover Upload Should Be Ready" in album_page
    assert "${cover_dir}    ${cover_name}=    Split Path" in album_page
    assert "document.body.innerText.includes(arguments[0])" in album_page
    assert "Cover Input Should Have File" not in album_page
    assert "Track Upload Should Be Ready" in album_page
    assert "${music_dir}    ${music_name}=    Split Path" in album_page
    assert album_page.count("document.body.innerText.includes(arguments[0])") == 2
    assert "Track Input Should Have File" not in album_page
    assert "normalize-space(@value)!=''" not in locators
    assert "Get Generated ISRC" in album_page
    assert "input[name='track:isrc[]']" in album_page
    assert ".map((element) => element.value.trim()).find(Boolean)" in album_page
    assert "${TRACK_ISRC_INPUT}" not in album_page
    assert "input[name='track:title[]']" in album_page
    assert "candidate.offsetParent !== null" in album_page
    assert "element.dispatchEvent(new Event(\"input\", {bubbles: true}))" in album_page
    assert "${TRACK_TITLE_INPUT}" not in album_page
    assert "@title='Add all to right side'" in locators
    assert " assigned " in locators
    assert "Assigned Platforms Should Exist" in album_page
    assert "No assigned DMB outlets found" in album_page
    assert "normalize-space()='<<'" not in locators
    assert "Wait Until Element Is Not Visible    ${ALL_PLATFORMS_BUTTON}" in album_page
    assert "${LOADING_OVERLAY}             id=vc_loading_layer_overlay" in locators
    assert album_page.count("Wait Until Element Is Not Visible    ${LOADING_OVERLAY}") == 2
    assert "Click Visible Exact Choice    ${dmb_genre}" in album_page
    assert "${GENRE_ID_INPUT}" in album_page
    assert "DMB genre ID was not committed" in album_page
    assert "${GENRE_PICKER}" in album_page
    assert "@name='genre_id'" in locators
    assert "dmb-icon--extract" in locators
    assert "/product/genre-chooser" in locators
    assert "Select Frame    ${GENRE_CHOOSER_IFRAME}" in album_page
    assert "Wait Until Keyword Succeeds    20s    500ms    Expand Genre Tree Parent    ${tree_parent}" in album_page
    assert "Select Genre Tree Value    ${tree_value}" in album_page
    assert "mat-tree-node .node-value span" in album_page
    assert 'input[type="radio"]:not([disabled])' in album_page
    assert "Wait Until Element Is Enabled    ${GENRE_PICKER_OK}" in album_page
    assert "dispatchEvent(new MouseEvent('click'" in album_page
    assert "Run Keyword And Return Status    Wait Until Element Is Visible" in album_page
    assert "Press Keys    ${locator}    ARROW_DOWN" in album_page
    assert "Press Keys    ${locator}    ENTER" in album_page
    assert "Field Value Should Equal" in album_page
    assert "window.jQuery(element).datepicker('setDate'" in album_page
    assert "window.jQuery(element).trigger('input').trigger('change')" in album_page
    assert "Date Value Should Match    ${actual_date}    ${date_value}" in album_page
    assert '"-".join(reversed($dotted_date.split(".")))' in album_page
    assert "$actual_date in ($dotted_date, $iso_date)" in album_page
    assert "Wait Until Element Is Not Visible    ${DATEPICKER}" in album_page
    assert "${DATEPICKER}                  xpath=//*[@id='ui-datepicker-div']" in locators
    assert "Capture Final Page Source" in album_page
    assert "${OUTPUT DIR}${/}final-state.html" in album_page
    assert "Capture Active Form Source" in create_suite
    assert "${OUTPUT DIR}${/}form-state.html" in album_page
    assert "Restore Album Frame After Contributor" in create_suite
    assert "Wait Until Element Is Visible    ${MAIN_IFRAME}" in album_page
    assert "Select Frame    ${MAIN_IFRAME}" in album_page
    assert "return document.documentElement.outerHTML;" in album_page
    assert "${source}=    Get Source" not in album_page
    assert "Select From List By Label    ${LABEL_SELECT}" in album_page
    assert "${JOB}[expiration_date]" in create_suite
    assert "Date Field Should Equal    ${SALES_START_DATE}" in album_page
    assert "Date Field Should Equal    ${SALES_END_DATE}" in album_page
    assert "${REVIEW_EAN_INPUT}" in album_page
    assert "${REVIEW_WIZARD_DATA}" in album_page
    assert "Review Wizard Value Should Equal    eanUpc" in album_page
    assert "Review Wizard List Should Contain    track:isrc" in album_page
    assert "Review Wizard List Should Contain    track:title" in album_page
    assert "Review Wizard List Should Contain    cce_aName" in album_page
    assert "Review Wizard Value Should Equal    genre" in album_page
    assert "Review Wizard Value Should Not Be Empty    genre_id" in album_page
    assert '$actual is not None and str($actual).strip() != ""' in album_page
    assert "JSON.parse(arguments[0].value)" in album_page
    assert "@name='_wizData'" in locators
    assert "normalize-space()='EAN/UPC'" in locators
    assert "Page Should Contain    ${title}" not in album_page
    assert "Page Should Contain    ${ean}" not in album_page
    assert album_page.count("Replace String    ${AJAX_EXACT_OPTION}") == 2
    assert "Press Keys    ${CONTRIBUTOR_NAME_INPUT}    TAB" in album_page
    assert "Press Keys    ${CONTRIBUTOR_NAME_INPUT}    ESC" not in album_page
    assert "const select = arguments[0]" in album_page
    assert "option.textContent.trim() === 'Performer'" in album_page
    assert "select.dispatchEvent(new Event('change', { bubbles: true }))" in album_page
    assert "Unselect All From List    ${CONTRIBUTOR_ROLES_SELECT}" not in album_page
    assert "Select From List By Label    ${CONTRIBUTOR_ROLES_SELECT}" not in album_page
    assert "Click Element    ${ADD_TRACKS_BUTTON}" not in album_page


def test_preflight_path_stops_before_submit_and_writes_no_checkpoint():
    suite = (ROOT / "automation" / "create_album.robot").read_text(encoding="utf-8")
    preflight = (ROOT / "preflight.py").read_text(encoding="utf-8")
    branch = suite.index("IF    '%{DMB_PREFLIGHT_ENABLED=false}' == 'true'")
    submit = suite.index("Submit Album And Verify Success", branch)
    assert branch < submit
    assert "Write Submit Checkpoint" not in suite[branch:submit]
    assert '"DMB_SUBMIT_ENABLED": "false"' in preflight


def test_create_submission_saves_then_publishes_exact_album():
    suite = (ROOT / "automation" / "create_album.robot").read_text(encoding="utf-8")
    page = (ROOT / "resources" / "pages" / "album_page.robot").read_text(
        encoding="utf-8"
    )

    assert "DMB_PUBLISH_ENABLED=false" in page
    assert "arguments[0].scrollIntoView({block: 'center'" in page
    assert "Scroll Element Into View    ${SAVE_BUTTON}" not in page
    save_click = (
        "Execute Javascript    arguments[0].click();    ARGUMENTS    ${save_button}"
    )
    submit = page.index("Submit Album And Verify Success")
    checkpoint = page.index("Write Submit Checkpoint", submit)
    save = page.index(save_click)
    publish_click = (
        "Execute Javascript    arguments[0].click();    ARGUMENTS    ${publish_button}"
    )
    publish = page.index(publish_click)
    assert save_click in page
    assert publish_click in page
    assert checkpoint < save < publish
    assert "Extract Dmb Release Id    ${saved_url}" in page
    assert "Should Be Equal As Strings    ${saved_ean}    ${ean}" in page
    assert "Created Album Publication Should Be Confirmed" in page
    assert "Submit Album And Verify Success" in suite


def test_publish_recovery_uses_checkpoint_and_exact_saved_album(tmp_path, monkeypatch):
    results = tmp_path / "results"
    checkpoint_path = results / "11" / "submit-started.json"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "release_id": 11,
                "ean_upc": "1234567890123",
                "isrcs": ["USABC2600001"],
                "title": "Safe Song",
                "started_at": "2026-10-04T12:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    checkpoint = recover_publish.load_checkpoint(checkpoint_path, 11)
    screenshot = results / "11" / "recovery" / "published.png"
    screenshot.parent.mkdir(parents=True)
    screenshot.write_bytes(b"png")
    result_path = screenshot.parent / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "submitted": True,
                "release_id": 11,
                "dmb_release_id": "2255903",
                "ean_upc": "1234567890123",
                "isrcs": ["USABC2600001"],
                "current_url": "https://dmb.kontornewmedia.com/page/album/2255903",
                "screenshot_path": str(screenshot),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(recover_publish, "RESULTS_DIR", results)

    payload = recover_publish.validate_result(
        result_path, 11, "2255903", checkpoint
    )
    assert payload["dmb_release_id"] == "2255903"


def test_publish_recovery_suite_cannot_create_or_save_an_album():
    suite = (ROOT / "automation" / "recover_publish.robot").read_text(
        encoding="utf-8"
    )
    locators = (ROOT / "resources" / "locators" / "album_locators.robot").read_text(
        encoding="utf-8"
    )

    assert "Publish Created Album And Verify Identity" in suite
    assert "Write Dmb Result" in suite
    assert "Navigate To Album Creation Form" not in suite
    assert "SAVE_BUTTON" not in suite
    assert "${CREATED_ALBUM_FORM_XPATH}" in locators
    assert "xpath=${CREATED_ALBUM_FORM}//" not in locators
    assert "input[@name='ean']" in locators
    assert "input[@name='ean' and @readonly]" not in locators


def test_success_suites_capture_full_final_page():
    for relative in (
        "automation/create_album.robot",
        "automation/edit_album.robot",
        "automation/recover_publish.robot",
    ):
        suite = (ROOT / relative).read_text(encoding="utf-8")
        assert "final-page-full.png" in suite
        assert "Capture Element Screenshot    xpath=//html" in suite


def test_edit_locators_compose_bare_xpath_roots():
    locators = (ROOT / "resources" / "locators" / "edit_album_locators.robot").read_text(
        encoding="utf-8"
    )

    assert "${EDIT_FORM_XPATH}" in locators
    assert "${TRACK_EDIT_FORM_XPATH}" in locators
    assert "${EDIT_CONTRIBUTOR_ROW_XPATH}" in locators
    assert "${TRACK_EDIT_CONTRIBUTOR_ROW_XPATH}" in locators
    assert "xpath=${EDIT_FORM}//" not in locators
    assert "xpath=${TRACK_EDIT_FORM}//" not in locators
    assert "xpath=(${EDIT_CONTRIBUTOR_ROW}//" not in locators
    assert "xpath=(${TRACK_EDIT_CONTRIBUTOR_ROW}//" not in locators
    assert "input[@name='ean']" in locators
    assert "input[@name='ean' and @readonly]" not in locators


def test_preflight_evidence_is_explicitly_not_submitted(tmp_path):
    screenshot = tmp_path / "review.png"
    screenshot.write_bytes(b"png")
    target = tmp_path / "preflight.json"

    dmb_job_module.DmbJob().write_dmb_preflight_result(
        str(target),
        42,
        "1234567890123",
        "USABC2600001",
        str(screenshot),
    )

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["submitted"] is False
    assert payload["release_id"] == 42
    assert payload["ean_upc"] == "1234567890123"
    assert payload["isrcs"] == ["USABC2600001"]


def test_linux_worker_uses_native_headless_firefox_without_xvfb():
    login_page = (ROOT / "resources" / "pages" / "login_page.robot").read_text(
        encoding="utf-8"
    )
    worker_source = (ROOT / "worker.py").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT.parent / "docker-compose.yml").read_text(encoding="utf-8")

    assert "FirefoxOptions" in login_page
    assert "-headless" in login_page
    assert "DMB_BROWSER_MODE" in worker_source
    assert '"xvfb-run"' not in worker_source
    assert "xvfb" not in dockerfile
    assert "DMB_BROWSER_MODE=${DMB_BROWSER_MODE:-headless}" in compose
    assert "/health/ready" in compose
    assert "shm_size: 512m" in compose


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
            "submission_fingerprint": "a" * 64,
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

    def fail_after_checkpoint(
        release_id,
        job_file,
        result_file,
        checkpoint_file,
        saved_checkpoint_file,
        expected_title,
    ):
        dmb_job_module.DmbJob().write_submit_checkpoint(
            str(checkpoint_file),
            release_id,
            "1234567890123",
            "USABC2600001",
                expected_title,
        )
        raise worker.DeliveryError("browser_lost_after_save")

    monkeypatch.setattr(worker, "run_robot", fail_after_checkpoint)
    report = MagicMock()
    monkeypatch.setattr(worker, "set_status", report)

    assert worker.process_release(release) == "uncertain"
    assert report.call_args.args == (42, "uncertain")
    assert "browser_lost_after_save" in report.call_args.kwargs["error"]
    assert report.call_args.kwargs["checkpoint"]["ean_upc"] == "1234567890123"
    assert len(report.call_args.kwargs["checkpoint"]["submission_fingerprint"]) == 64


def test_saved_checkpoint_keeps_exact_remote_album(tmp_path):
    checkpoint = tmp_path / "saved.json"
    dmb_job_module.DmbJob().write_saved_checkpoint(
        str(checkpoint),
        42,
        "2255903",
        "1234567890123",
        "USABC2600001",
        "Safe Title",
        "https://dmb.kontornewmedia.com/page/album/2255903",
    )
    loaded = worker.load_saved_checkpoint(checkpoint, 42, "Safe Title")
    assert loaded["dmb_release_id"] == "2255903"
    assert loaded["submission_fingerprint"] == worker.submission_fingerprint(
        42, "Safe Title", "1234567890123", ["USABC2600001"]
    )


def test_recovery_checkpoint_rejects_changed_release_identity():
    release = sample_release()
    release.update(
        {
            "dmb_release_id": "2255903",
            "dmb_ean_upc": "1234567890123",
            "dmb_isrcs": ["USABC2600001"],
            "dmb_submission_fingerprint": "bad",
        }
    )
    with pytest.raises(worker.DeliveryError, match="dmb_recovery_checkpoint_invalid"):
        worker.recovery_checkpoint_from_release(release)


def test_recovery_reuses_verified_result_without_new_browser(tmp_path, monkeypatch):
    release = sample_release()
    fingerprint = worker.submission_fingerprint(
        42, "Safe Title", "1234567890123", ["USABC2600001"]
    )
    release.update(
        {
            "song_name": "Safe Title",
            "dmb_release_id": "2255903",
            "dmb_ean_upc": "1234567890123",
            "dmb_isrcs": ["USABC2600001"],
            "dmb_submission_fingerprint": fingerprint,
        }
    )
    monkeypatch.setattr(worker, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        worker,
        "run_recovery_robot",
        lambda checkpoint, result_file: {
            "dmb_release_id": checkpoint["dmb_release_id"],
            "ean_upc": checkpoint["ean_upc"],
            "isrcs": checkpoint["isrcs"],
            "evidence_path": "results/42",
            "submission_fingerprint": checkpoint["submission_fingerprint"],
        },
    )
    report = MagicMock()
    monkeypatch.setattr(worker, "set_status", report)
    assert worker.process_recovery_release(release) == "completed"
    assert report.call_args.args == (42, "completed")
