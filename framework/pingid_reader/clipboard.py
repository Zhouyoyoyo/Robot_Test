import time
import re
import win32clipboard
from .logger import get_logger

log = get_logger()


def clear_clipboard():
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        log.info("Clipboard cleared")
    except Exception as e:
        log.warning(f"Failed to clear clipboard: {e}")


def read_otp_from_clipboard(timeout_sec: float = 3.0) -> str:
    """
    从系统剪贴板中读取 6 位 OTP
    """
    end = time.time() + timeout_sec

    while time.time() < end:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            if isinstance(data, str):
                log.info(f"Clipboard content: {data!r}")
                m = re.search(r"\b\d{6}\b", data)
                if m:
                    return m.group()

        except Exception:
            pass

        time.sleep(0.05)

    raise RuntimeError("Failed to read OTP from clipboard")
