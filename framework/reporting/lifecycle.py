"""用例生命周期模块。

Case lifecycle module.

作者: taobo.zhou
Author: taobo.zhou
"""


def on_case_finished(item, report, driver):
    from pathlib import Path

    from framework.utils.screenshot import take_screenshot

    if report.when == "call":
        screenshot_dir = Path("output/screenshots")
        case_id = item.nodeid.replace("/", "_").replace("::", "__")
        return take_screenshot(driver, str(screenshot_dir), prefix=case_id)
    return None
