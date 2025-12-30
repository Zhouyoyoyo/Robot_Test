"""PingID OTP 管理模块。

PingID OTP manager module.

Author: taobo.zhou
"""

import threading
from contextlib import contextmanager
import time
import subprocess
from time import sleep

import psutil
from pathlib import Path

from framework.utils.config_loader import load_config
from .window import (
    wait_for_pingid_window,
    normalize_pingid_window,
    click_copy_button,
)
from .clipboard import clear_clipboard, read_otp_from_clipboard
from .logger import get_logger

log = get_logger()


class PingIDOtpManager:
    """PingID OTP 管理器。

    PingID OTP manager.

    Author: taobo.zhou
    """
    _instance = None
    _lock = threading.Lock()
    _use_lock = threading.Lock()

    def __init__(self):
        self._ready = False
        self._hwnd = None

        cfg = load_config()
        pingid_cfg = cfg.get("pingid", {})

        self.exe_path = Path(pingid_cfg.get("exe_path", ""))
        self.window_title_keyword = pingid_cfg.get("window_title_keyword", "PingID")

        self.clean_start = pingid_cfg.get("clean_start", True)

        window_cfg = pingid_cfg.get("window", {})
        self.window_wait_timeout = window_cfg.get("wait_timeout", 15)
        self.min_width = window_cfg.get("min_width", 520)
        self.min_height = window_cfg.get("min_height", 320)

        clipboard_cfg = pingid_cfg.get("clipboard", {})
        self.clipboard_read_timeout = float(clipboard_cfg.get("read_timeout", 3.0))

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = PingIDOtpManager()
            return cls._instance

    def ensure_ready(self):
        if self._ready and self._hwnd:
            return

        log.info("Ensuring PingID is ready")

        if self.clean_start:
            self._kill_existing_pingid_processes()

        if not self._is_pingid_running():
            self._start_pingid()

        self._hwnd = wait_for_pingid_window(
            title_keyword=self.window_title_keyword,
            timeout=self.window_wait_timeout,
        )

        normalize_pingid_window(
            self._hwnd,
            min_width=self.min_width,
            min_height=self.min_height,
        )

        self._ready = True
        log.info("PingID ready")

    def shutdown(self):
        log.info("[PingID] shutdown")

        try:
            for proc in psutil.process_iter(attrs=["name"]):
                if proc.info["name"] and proc.info["name"].lower() == "pingid.exe":
                    proc.kill()
        except Exception as e:
            log.warning(f"[PingID] shutdown kill failed: {e}")

        self._ready = False
        self._hwnd = None

    def _is_pingid_running(self) -> bool:
        for proc in psutil.process_iter(attrs=["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name == "pingid.exe":
                    return True
            except Exception:
                pass
        return False

    def _kill_existing_pingid_processes(self):
        killed_pids = []
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name == "pingid.exe":
                    pid = proc.info.get("pid")
                    proc.kill()
                    killed_pids.append(pid)
            except Exception as e:
                log.warning(f"Kill PingID process failed: {e}")

        if killed_pids:
            log.warning(f"PingID residual processes killed: {killed_pids}")
            time.sleep(1.5)

    def _start_pingid(self):
        if not self.exe_path or not self.exe_path.exists():
            raise FileNotFoundError(f"PingID exe not found: {self.exe_path}")

        log.info(f"Starting PingID: {self.exe_path}")
        subprocess.Popen([str(self.exe_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def copy_otp(self) -> str:
        self.ensure_ready()

        clear_clipboard()
        sleep(0.8)
        click_copy_button(self._hwnd)

        otp = read_otp_from_clipboard(self.clipboard_read_timeout)
        if not otp:
            raise TimeoutError("Read OTP from clipboard timeout")
        return otp

    @contextmanager
    def exclusive(self, shutdown_after: bool = True):
        PingIDOtpManager._use_lock.acquire()
        try:
            yield self
        finally:
            try:
                if shutdown_after:
                    self.shutdown()
            finally:
                PingIDOtpManager._use_lock.release()
