import importlib
from types import SimpleNamespace

import pytest


def _load_bot(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_TOKEN", "123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ADMIN_GROUP_ID", "-1004452282696")
    monkeypatch.setenv("MANAGER_IDS", "99")
    monkeypatch.setenv("DMB_SUCCESS_TOPIC_ID", "44")
    monkeypatch.setenv("DMB_ERROR_TOPIC_ID", "43")
    monkeypatch.setenv("DMB_REVIEW_TOPIC_ID", "42")
    monkeypatch.setenv("DMB_RECOVERY_ENABLED", "true")
    monkeypatch.setenv("DMB_RESULTS_ROOT", str(tmp_path))
    bot = importlib.import_module("bot")
    monkeypatch.setattr(bot, "ADMIN_GROUP_ID", "-1004452282696")
    monkeypatch.setattr(bot, "MANAGER_IDS", {99})
    monkeypatch.setattr(bot, "DMB_SUCCESS_TOPIC_ID", 44)
    monkeypatch.setattr(bot, "DMB_ERROR_TOPIC_ID", 43)
    monkeypatch.setattr(bot, "DMB_REVIEW_TOPIC_ID", 42)
    monkeypatch.setattr(bot, "DMB_RECOVERY_ENABLED", True)
    monkeypatch.setattr(bot, "DMB_RESULTS_ROOT", tmp_path.resolve())
    return bot


def test_dmb_report_buttons_are_bound_to_release_and_attempt(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    retry_release = SimpleNamespace(
        id=7,
        status="dmb_retry_waiting",
        dmb_attempts=1,
        dmb_submission_started_at=None,
        dmb_submission_fingerprint=None,
        is_edit=False,
    )
    retry = bot._dmb_report_keyboard(retry_release, "error", 1)
    assert retry.inline_keyboard[0][0].callback_data == "dmb_retry_7_1"

    review_release = SimpleNamespace(
        id=8,
        status="dmb_verification_required",
        dmb_attempts=2,
        dmb_release_id="2255903",
        dmb_ean_upc="1234567890123",
        dmb_isrcs=["USABC2600001"],
        dmb_submission_fingerprint="a" * 64,
        is_edit=False,
    )
    resume = bot._dmb_report_keyboard(review_release, "review", 2)
    assert resume.inline_keyboard[0][0].callback_data == "dmb_resume_8_2"
    assert resume.inline_keyboard[0][0].text == "🔁 تلاش مجدد امن"


def test_dmb_evidence_never_escapes_release_directory(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    release_dir = tmp_path / "7"
    release_dir.mkdir()
    image = release_dir / "final-state.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    assert bot._dmb_evidence_image("results/7", 7)[1] == "final-state.png"
    assert bot._dmb_evidence_image("results/8/../7/final-state.png", 7) is None


def _report_release(**updates):
    values = {
        "id": 21,
        "user_id": 8001,
        "song_name": "Night Track",
        "artist_name": "Test Artist",
        "is_edit": False,
        "status": "dmb_verification_required",
        "dmb_attempts": 2,
        "dmb_release_id": "2255903",
        "dmb_ean_upc": "1234567890123",
        "dmb_isrcs": ["USABC2600001"],
        "dmb_submission_fingerprint": "a" * 64,
        "dmb_submission_started_at": None,
        "dmb_last_error": "publish_not_confirmed",
        "dmb_evidence_path": "results/21",
    }
    values.update(updates)
    return SimpleNamespace(**values)


def test_dmb_report_texts_are_distinct_useful_and_have_no_version(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    release = _report_release()
    success_topic, success, _ = bot._dmb_report_content(
        release, "success", {"attempt": 2}
    )
    error_topic, error, _ = bot._dmb_report_content(
        release, "error", {"attempt": 2, "error": "network_failed"}
    )
    review_topic, review, keyboard = bot._dmb_report_content(
        release, "review", {"attempt": 2, "error": "publish_not_confirmed"}
    )
    assert (success_topic, error_topic, review_topic) == (44, 43, 42)
    for text in (success, error, review):
        assert "Night Track" in text
        assert "ID سفارش: 21" in text
        assert "0.9.0" not in text
        assert "نسخه" not in text
        assert len(text) <= 1000
    assert "تصویر کامل صفحه نهایی" in success
    assert "مرحله:" in error
    assert "ID ذخیره‌شده DMB: 2255903" in review
    assert "کار بعدی:" in review
    assert review != error
    assert keyboard.inline_keyboard[0][0].text == "🔁 تلاش مجدد امن"


def test_success_report_only_accepts_final_success_image(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    release_dir = tmp_path / "21"
    release_dir.mkdir()
    (release_dir / "final-state.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"x" * 200
    )
    assert bot._dmb_evidence_image("results/21", 21, "success") is None
    final_image = release_dir / "final-page-full.png"
    final_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"y" * 200)
    evidence = bot._dmb_evidence_image("results/21", 21, "success")
    assert evidence is not None
    assert evidence[1] == "final-page-full.png"


@pytest.mark.asyncio
async def test_success_report_fails_closed_without_final_image(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    release = _report_release()
    with pytest.raises(RuntimeError, match="dmb_success_evidence_missing"):
        await bot.notify_admin_dmb_report(release, "success", {"attempt": 2})


def test_unknown_dmb_report_event_fails_closed(monkeypatch, tmp_path):
    bot = _load_bot(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError, match="dmb_report_event_invalid"):
        bot._dmb_report_content(_report_release(), "unknown", {})
