import threading
from contextlib import contextmanager
import time
import subprocess
from time import sleep

import psutil
from pathlib import Path

from framework.utils.config_loader import load_config
from .global_lock import pingid_global_lock
from .window import (
    wait_for_pingid_window,
    normalize_pingid_window,
    click_copy_button,
)
from .clipboard import clear_clipboard, read_otp_from_clipboard
from .logger import get_logger

log = get_logger()


class PingIDOtpManager:
    """Author: taobo.zhou
    中文：PingID OTP 管理器，负责启动与读取验证码。
    English: PingID OTP manager responsible for startup and OTP retrieval.
    """

    _instance = None
    _lock = threading.Lock()
    _use_lock = threading.Lock()

    def __init__(self):
        """Author: taobo.zhou
        中文：初始化 PingID 配置与运行状态。
        参数: 无。
        """

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
        """Author: taobo.zhou
        中文：获取 PingIDOtpManager 单例实例。
        参数:
            cls: 类对象。
        """

        with cls._lock:
            if cls._instance is None:
                cls._instance = PingIDOtpManager()
            return cls._instance

    def ensure_ready(self):
        """Author: taobo.zhou
        中文：确保 PingID 应用已启动并可用。
        参数: 无。
        """

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
        """Author: taobo.zhou
        中文：关闭 PingID 应用并重置状态。
        参数: 无。
        """

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
        """Author: taobo.zhou
        中文：判断 PingID 进程是否正在运行。
        参数: 无。
        """

        for proc in psutil.process_iter(attrs=["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name == "pingid.exe":
                    return True
            except Exception:
                pass
        return False

    def _kill_existing_pingid_processes(self):
        """Author: taobo.zhou
        中文：强制关闭现有 PingID 进程。
        参数: 无。
        """

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
        """Author: taobo.zhou
        中文：启动 PingID 应用。
        参数: 无。
        """

        if not self.exe_path or not self.exe_path.exists():
            raise FileNotFoundError(f"PingID exe not found: {self.exe_path}")

        log.info(f"Starting PingID: {self.exe_path}")
        subprocess.Popen([str(self.exe_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def copy_otp(self) -> str:
        """Author: taobo.zhou
        中文：复制并返回 PingID OTP 验证码。
        参数: 无。
        """

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
        """Author: taobo.zhou
        中文：在全局锁内独占使用 PingID。
        参数:
            shutdown_after: 是否在结束后关闭 PingID。
        """

        with pingid_global_lock():
            PingIDOtpManager._use_lock.acquire()
            try:
                yield self
            finally:
                try:
                    if shutdown_after:
                        self.shutdown()
                finally:
                    PingIDOtpManager._use_lock.release()
