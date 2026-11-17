import importlib.util
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

spec = importlib.util.spec_from_file_location(
    "dmb_session", Path(__file__).parents[1] / "libraries/dmb_session.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("DMB_SESSION_DIR", str(tmp_path))
    monkeypatch.setenv("DMB_USERNAME", "test-account")
    monkeypatch.setenv("DMB_PASSWORD", "test-password")
    item = module.DmbSession()
    item.acquire_dmb_session()
    yield item
    item.release_dmb_session()


def authenticate(item, driver):
    driver.find_elements.return_value = [MagicMock()]
    if not isinstance(driver.get_cookies.return_value, list):
        driver.get_cookies.return_value = []
    with patch.object(module, "BuiltIn") as builtin:
        builtin.return_value.get_library_instance.return_value.driver = driver
        item.ensure_dmb_authenticated()


def test_reused_cookie_session_never_submits_credentials(session):
    driver = MagicMock()
    session.state = {"cookies": [{"name": "session", "value": "opaque", "domain": session.HOST}]}
    with patch.object(session, "_authenticated", side_effect=[False, True]):
        authenticate(session, driver)
    driver.add_cookie.assert_called_once()
    driver.find_element.assert_not_called()


def test_expired_session_logs_in_once_and_saves_for_next_process(session):
    driver = MagicMock()
    driver.get_cookies.return_value = [{"name": "session", "value": "new", "domain": session.HOST}]
    with patch.object(session, "_authenticated", side_effect=[False, False, True]):
        authenticate(session, driver)
    assert driver.find_element.return_value.click.call_count == 1
    state = json.loads(session.path.read_text())
    assert state["cookies"][0]["value"] == "new"
    assert state["login_blocked_until"] == 0


def test_failed_login_cooldown_survives_process_restart(session):
    driver = MagicMock()
    session.state["login_blocked_until"] = time.time() + 1800
    session._write()
    session.release_dmb_session()
    session.acquire_dmb_session()
    with patch.object(session, "_authenticated", return_value=False):
        with pytest.raises(RuntimeError, match="cooldown"):
            authenticate(session, driver)
    driver.find_element.assert_not_called()


def test_concurrent_order_cannot_use_same_browser(session):
    other = module.DmbSession()
    with pytest.raises(RuntimeError, match="session_busy"):
        other.acquire_dmb_session()


def test_foreign_cookies_rejected_before_browser_mutation(session):
    driver = MagicMock()
    session.state = {"cookies": [{"name": "session", "value": "x", "domain": "other.example"}]}
    with patch.object(session, "_authenticated", return_value=False):
        with pytest.raises(RuntimeError, match="cookie_domain"):
            authenticate(session, driver)
    driver.add_cookie.assert_not_called()
    driver.find_element.assert_not_called()


def test_browser_is_reattached_without_new_driver_or_login(session):
    session.state["browser"] = {"port": 12345, "session_id": "existing", "capabilities": {}}
    with patch.object(module, "AttachedFirefox") as attached, patch.object(module, "BuiltIn"), patch.object(module.subprocess, "Popen") as launch:
        session.open_persistent_dmb_browser()
    launch.assert_not_called()
    attached.assert_called_once_with("http://127.0.0.1:12345", "existing", {})


def test_release_retains_authenticated_browser(session):
    driver = MagicMock()
    session.driver = driver
    session.release_dmb_session()
    driver.quit.assert_not_called()


def test_unspecified_samesite_cookie_roundtrips_without_browser_rejection(session):
    driver = MagicMock()
    original = {"name": "csrf", "value": "opaque", "domain": session.HOST,
                "sameSite": "None", "secure": False}
    session.state["cookies"] = [original]
    with patch.object(session, "_authenticated", side_effect=[False, True]):
        authenticate(session, driver)
    assert "sameSite" not in driver.add_cookie.call_args.args[0]
    assert original["sameSite"] == "None"


def test_diagnostic_retry_cannot_submit_credentials(session, monkeypatch):
    monkeypatch.setenv("DMB_LOGIN_ALLOWED", "false")
    driver = MagicMock()
    with patch.object(session, "_authenticated", return_value=False):
        with pytest.raises(RuntimeError, match="login_disabled"):
            authenticate(session, driver)
    driver.find_element.assert_not_called()
