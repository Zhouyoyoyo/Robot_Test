"""测试夹具模块。

Test fixture module.

Author: taobo.zhou
"""

from pathlib import Path

import pytest

from framework.core.driver_manager import DriverManager
from framework.utils.config_loader import load_config
from framework.utils.locator_loader import LocatorLoader
from framework.reporting.lifecycle import on_case_finished
from framework.utils.screenshot import take_screenshot


@pytest.fixture(scope="session")
def config():
    cfg = load_config()

    project_root = Path(cfg.get("_project_root", "."))
    if "paths" in cfg and isinstance(cfg["paths"], dict):
        for k, v in list(cfg["paths"].items()):
            if isinstance(v, str) and v and not Path(v).is_absolute():
                cfg["paths"][k] = str((project_root / v).resolve())

    locator_path = cfg["paths"]["locator"]
    loader = LocatorLoader(locator_path)
    loader.validate_all()
    cfg["locator_loader"] = loader

    return cfg


def capture_final_screenshot(driver, case_id: str, cfg: dict | None = None) -> str | None:
    try:
        folder = "output/screenshots"
        if cfg and isinstance(cfg, dict):
            folder = (cfg.get("paths") or {}).get("screenshots", folder)
        return take_screenshot(driver, folder, prefix=case_id)
    except Exception:
        return None


@pytest.fixture(scope="session")
def driver(config, request):
    driver = DriverManager.get_driver()
    request.session.driver = driver

    selenium_cfg = config.get("selenium", {}) or {}
    implicit_wait = selenium_cfg.get("implicit_wait")
    if implicit_wait is not None:
        try:
            driver.implicitly_wait(float(implicit_wait))
        except Exception:
            pass

    page_load_timeout = selenium_cfg.get("page_load_timeout")
    if page_load_timeout is not None:
        try:
            driver.set_page_load_timeout(float(page_load_timeout))
        except Exception:
            pass

    yield driver
    DriverManager.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        driver = getattr(item.session, "driver", None)
        if not driver:
            return

        path = on_case_finished(item, rep, driver)

        setattr(item, "final_screenshot", path)
