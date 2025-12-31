import time
import psutil
import win32gui
import win32con
import win32process
import win32api
import ctypes

from .logger import get_logger

log = get_logger()


def find_pingid_hwnd(window_title_keyword: str) -> int | None:
    """Author: taobo.zhou
    根据窗口标题关键字查找 PingID 窗口句柄。
    
        window_title_keyword: 窗口标题关键字。
    """

    result = None

    def enum_handler(hwnd, _):
        """Author: taobo.zhou
        枚举窗口句柄并匹配 PingID 窗口。
        
            hwnd: 窗口句柄。
            _: 预留参数，占位。
        """

        nonlocal result
        if result:
            return

        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd) or ""
        if window_title_keyword not in title:
            return

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            if psutil.Process(pid).name().lower() == "pingid.exe":
                result = hwnd
        except Exception:
            pass

    win32gui.EnumWindows(enum_handler, None)
    return result


def wait_for_pingid_window(
    *,
    title_keyword: str,
    timeout: float,
    poll_interval: float = 0.25,
) -> int:
    """Author: taobo.zhou
    等待 PingID 窗口出现并返回句柄。
    
        title_keyword: 窗口标题关键字。
        timeout: 最大等待时间（秒）。
        poll_interval: 轮询间隔（秒）。
    """

    end_time = time.time() + timeout

    while time.time() < end_time:
        hwnd = find_pingid_hwnd(title_keyword)
        if hwnd:
            log.info("PingID window detected")
            return hwnd
        time.sleep(poll_interval)

    raise TimeoutError(
        f"PingID window not found within {timeout} seconds "
        f"(title_keyword={title_keyword!r})"
    )


def normalize_pingid_window(
    hwnd: int,
    *,
    min_width: int,
    min_height: int,
):
    """Author: taobo.zhou
    恢复并调整 PingID 窗口大小。
    
        hwnd: PingID 窗口句柄。
        min_width: 窗口最小宽度。
        min_height: 窗口最小高度。
    """

    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)

    time.sleep(0.3)

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    target_width = max(width, min_width)
    target_height = max(height, min_height)

    if width < target_width or height < target_height:
        log.info(
            f"Resizing PingID window: "
            f"{width}x{height} -> {target_width}x{target_height}"
        )
        win32gui.MoveWindow(
            hwnd,
            left,
            top,
            target_width,
            target_height,
            True,
        )
        time.sleep(0.3)


def click_copy_button(hwnd: int):
    """Author: taobo.zhou
    点击 PingID 窗口中的复制按钮。
    
        hwnd: PingID 窗口句柄。
    """

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    x = left + int(width * 0.72)
    y = top + int(height * 0.78)

    log.info(f"Clicking copy button at ({x}, {y})")

    win32api.SetCursorPos((x, y))
    time.sleep(0.05)

    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    time.sleep(0.3)
