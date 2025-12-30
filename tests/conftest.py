"""测试夹具模块。

Test fixture module.

Author: taobo.zhou
"""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from framework.core.driver_manager import DriverManager
from framework.utils.config_loader import load_config
from framework.utils.excel_loader import load_excel_kv
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


def pytest_generate_tests(metafunc):
    """
    负责把 Excel 的每个 sheet 变成一个 pytest 参数化用例。
    失败重跑时，pytest 会再次用相同的 sheet_name 调用该用例，因此会使用同一份 sheet 数据。
    """
    if "sheet_name" not in metafunc.fixturenames:
        return

    # 这里必须独立加载配置，不能依赖任何 pytest 内部字段（禁止使用 metafunc.config._store 之类的非标准对象）
    cfg = load_config()

    project_root = Path(cfg.get("_project_root", "."))
    data_path = cfg["paths"]["data"]
    if isinstance(data_path, str) and data_path and not Path(data_path).is_absolute():
        data_path = str((project_root / data_path).resolve())

    if not Path(data_path).exists():
        raise RuntimeError(f"Excel 数据文件不存在: {data_path}")

    wb = load_workbook(data_path, read_only=True, data_only=True)
    sheet_names = wb.sheetnames

    # 强制：只允许 sheet 名为 "1" 和 "2"
    # 若 Excel 多了或少了 sheet，直接失败，让用户修 Excel
    if sheet_names != ["1", "2"]:
        raise RuntimeError(f"Excel 的 sheet 必须严格为 ['1','2']，当前为: {sheet_names}")

    metafunc.parametrize(
        "sheet_name",
        sheet_names,
        ids=[f"sheet={name}" for name in sheet_names],
    )


@pytest.fixture
def case_data(config, sheet_name):
    # 永远只读取当前 sheet_name 的数据，失败重跑仍然使用同一 sheet_name
    return load_excel_kv(config["paths"]["data"], sheet_name)


@pytest.fixture
def base_url(config, sheet_name):
    # base_url 只能来自 config.yaml: project.urls
    urls = config["project"]["urls"]
    if sheet_name not in urls:
        raise RuntimeError(f"config.yaml 中 project.urls 未配置 sheet [{sheet_name}] 的 URL")
    return urls[sheet_name]
