import os
from datetime import datetime


def take_screenshot(
    driver,
    folder: str,
    prefix: str = "case",
    stable: bool = False,
) -> str:
    """Author: taobo.zhou
    中文：保存截图并返回文件路径。
    参数:
        driver: WebDriver 实例。
        folder: 截图输出目录。
        prefix: 文件名前缀。
        stable: 是否使用固定文件名。
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
