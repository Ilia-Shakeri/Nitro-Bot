"""Reuse the authenticated site session across isolated delivery processes."""

import hashlib
import json
import os
import socket
import subprocess
import time
from pathlib import Path

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver


class AttachedFirefox(webdriver.Remote):
    def __init__(self, endpoint, session_id, capabilities):
        self.existing_session = session_id
        self.existing_capabilities = capabilities
        super().__init__(command_executor=endpoint, options=webdriver.FirefoxOptions())

    def start_session(self, capabilities):
        self.session_id = self.existing_session
        self.caps = self.existing_capabilities


class DmbSession:
    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_AUTO_KEYWORDS = False
    HOST = "dmb.kontornewmedia.com"
    MENU = "//div[contains(@class,'text-label') and (normalize-space()='Music' or normalize-space()='Audio')]"

    def __init__(self):
        self.lock = None
        self.path = None
        self.driver = None
        self.state = {}

    @keyword
    def acquire_dmb_session(self):
        # A separate directory keeps credentials out of delivery evidence and reports.
        root = Path(os.getenv("DMB_SESSION_DIR", "/app/session"))
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(root, 0o700)
        account = hashlib.sha256(os.environ["DMB_USERNAME"].encode()).hexdigest()[:24]
        self.path = root / f"{account}.json"
        self.lock = (root / f"{account}.lock").open("a+")
        os.chmod(root / f"{account}.lock", 0o600)
        try:
            if os.name == "nt":
                import msvcrt
                self.lock.seek(0)
                self.lock.write("0")
                self.lock.flush()
                self.lock.seek(0)
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            self.lock = None
            raise RuntimeError("DMB_session_busy") from None
        try:
            self.state = json.loads(self.path.read_text()) if self.path.exists() else {}
            if not isinstance(self.state, dict):
                raise ValueError()
        except (ValueError, OSError):
            self.release_dmb_session()
            raise RuntimeError("DMB_session_state_invalid") from None

    def _write(self):
        temporary = self.path.with_suffix(".tmp")
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(self.state, stream)
        os.chmod(temporary, 0o600)
        temporary.replace(self.path)

    @keyword
    def open_persistent_dmb_browser(self, mode="headless"):
        if mode not in {"headless", "visible"} or self.lock is None:
            raise RuntimeError("DMB_browser_configuration_invalid")
        selenium = BuiltIn().get_library_instance("SeleniumLibrary")
        saved = self.state.get("browser", {})
        port = saved.get("port")
        if isinstance(port, int) and 1024 <= port <= 65535:
            try:
                self.driver = AttachedFirefox(
                    f"http://127.0.0.1:{port}", saved["session_id"], saved["capabilities"]
                )
                if not self.driver.window_handles:
                    self.driver = None
            except Exception:
                self.driver = None
        if self.driver is None:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
            process = subprocess.Popen(
                ["geckodriver", "--host", "127.0.0.1", "--port", str(port)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True,
            )
            try:
                def ready(_):
                    if process.poll() is not None:
                        raise RuntimeError("DMB_browser_service_failed")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=1):
                            return True
                    except OSError:
                        return False
                WebDriverWait(None, 15).until(ready)
                options = webdriver.FirefoxOptions()
                if mode == "headless":
                    options.add_argument("-headless")
                self.driver = webdriver.Remote(
                    command_executor=f"http://127.0.0.1:{port}", options=options
                )
            except Exception:
                process.terminate()
                raise
            self.state["browser"] = {
                "port": port, "session_id": self.driver.session_id,
                "capabilities": self.driver.capabilities,
            }
            self._write()
        selenium.register_driver(self.driver, "dmb")
        self.driver.set_window_size(1366, 768)
        self.driver.get(f"https://{self.HOST}/")

    def _authenticated(self):
        return any(e.is_displayed() for e in self.driver.find_elements(By.XPATH, self.MENU))

    def _page_state(self, _):
        if self._authenticated():
            return "authenticated"
        if any(e.is_displayed() for e in self.driver.find_elements(By.CSS_SELECTOR, "dmb-input#user input")):
            return "login"
        return False

    @keyword
    def ensure_dmb_authenticated(self):
        if self.lock is None:
            raise RuntimeError("DMB_session_lock_missing")
        self.driver = BuiltIn().get_library_instance("SeleniumLibrary").driver
        self.driver.switch_to.default_content()
        page = WebDriverWait(self.driver, 45).until(self._page_state)
        if page != "authenticated":
            for cookie in self.state.get("cookies", []):
                domain = cookie.get("domain", "").lstrip(".")
                if domain not in {self.HOST, "kontornewmedia.com"}:
                    raise RuntimeError("DMB_session_cookie_domain_invalid")
                if cookie.get("expiry", time.time() + 1) <= time.time():
                    continue
                cookie = dict(cookie)
                # Firefox may report None for an unspecified SameSite attribute.
                # Replaying that as explicit None requires Secure and gets rejected.
                if cookie.get("sameSite") == "None" and not cookie.get("secure"):
                    cookie.pop("sameSite")
                self.driver.add_cookie(cookie)
            if self.state.get("cookies"):
                self.driver.get(f"https://{self.HOST}/")
            page = WebDriverWait(self.driver, 45).until(self._page_state)
        if page != "authenticated":
            if os.getenv("DMB_LOGIN_ALLOWED", "true").lower() != "true":
                raise RuntimeError("DMB_session_expired_login_disabled")
            # Persist before clicking: crashes and restarts must not send more login mail.
            if time.time() < self.state.get("login_blocked_until", 0):
                raise RuntimeError("DMB_login_cooldown_active")
            self.state["login_blocked_until"] = time.time() + 1800
            self._write()
            self.driver.find_element(By.CSS_SELECTOR, "dmb-input#user input").send_keys(os.environ["DMB_USERNAME"])
            self.driver.find_element(By.CSS_SELECTOR, "dmb-input#pass input").send_keys(os.environ["DMB_PASSWORD"])
            self.driver.find_element(By.CSS_SELECTOR, "dmb-button[type='submit'] button[type='submit']").click()
            WebDriverWait(self.driver, 60).until(lambda _: self._authenticated())
        self.state["login_blocked_until"] = 0
        self.save_dmb_session()

    @keyword
    def save_dmb_session(self):
        if self.lock is not None and self.driver is not None:
            self.driver.switch_to.default_content()
            # Retain cookies even when the current screen is a loading/error page.
            cookies = self.driver.get_cookies()
            if cookies:
                self.state["cookies"] = cookies
                self._write()

    @keyword
    def release_dmb_session(self):
        if self.lock is not None:
            self.lock.close()
            self.lock = None


# Robot's file import resolves the library class by the module filename.
dmb_session = DmbSession
