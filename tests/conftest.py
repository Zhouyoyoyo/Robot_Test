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

import pytest
from openpyxl import load_workbook
from framework.utils.excel_loader import load_excel_kv


def pytest_generate_tests(metafunc):
    """
    这里负责决定：测试要跑哪些 sheet。
    """
    if "sheet_name" in metafunc.fixturenames:
        config = metafunc.config._store.get("config_obj")
        if config is None:
            from framework.utils.config_loader import load_config
            config = load_config()

        excel_path = config["paths"]["data"]
        wb = load_workbook(excel_path, read_only=True, data_only=True)

        sheet_names = wb.sheetnames

        if not sheet_names:
            raise RuntimeError("Excel 中没有任何 sheet")

        metafunc.parametrize(
            "sheet_name",
            sheet_names,
            ids=[f"sheet={name}" for name in sheet_names],
        )


@pytest.fixture
def case_data(config, sheet_name):
    """
    case_data 永远只来自当前 sheet_name
    """
    return load_excel_kv(
        config["paths"]["data"],
        sheet_name,
    )


@pytest.fixture
def base_url(config, sheet_name):
    """
    base_url 只允许来自 project.urls
    """
    urls = config.get("project", {}).get("urls")

    if not isinstance(urls, dict):
        raise RuntimeError("config.yaml 中缺少 project.urls")

    if sheet_name not in urls:
        raise RuntimeError(
            f"project.urls 中未配置 sheet [{sheet_name}] 的 URL"
        )

    return urls[sheet_name]
