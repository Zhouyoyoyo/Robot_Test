"""截图工具模块。

Screenshot utility module.

Author: taobo.zhou
"""

import os
from datetime import datetime


def take_screenshot(
    driver,
    folder: str,
    prefix: str = "case",
    stable: bool = False,
) -> str:
    """
    Take screenshot.

    :param driver: selenium driver
    :param folder: output folder
    :param prefix: case identifier (建议传入 nodeid 处理后的唯一前缀)
    :param stable: True 时使用固定文件名 {prefix}.png（可覆盖，适合重跑收口）
                  False 时使用带时间戳文件名（默认兼容旧逻辑）
    """
    os.makedirs(folder, exist_ok=True)

    if stable:
        filename = f"{prefix}.png"
        path = os.path.join(folder, filename)
        driver.save_screenshot(path)
        return path

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefix}_{ts}_{os.getpid()}.png"
    path = os.path.join(folder, filename)
    driver.save_screenshot(path)
    return path
