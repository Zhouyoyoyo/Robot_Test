import pytest
from framework.utils.config_loader import load_config
from framework.utils.locator_loader import LocatorLoader
from framework.utils.screenshot import take_screenshot


@pytest.fixture(scope="session")
def config():
    cfg = load_config()

    # 将 paths 里的相对路径统一转换成绝对路径，避免从不同工作目录运行时找不到文件
    from pathlib import Path
    project_root = Path(cfg.get("_project_root", "."))
    if "paths" in cfg and isinstance(cfg["paths"], dict):
        for k, v in list(cfg["paths"].items()):
            if isinstance(v, str) and v and not Path(v).is_absolute():
                cfg["paths"][k] = str((project_root / v).resolve())

    # locator loader
    locator_path = cfg["paths"]["locator"]
    loader = LocatorLoader(locator_path)
    loader.validate_all()
    cfg["locator_loader"] = loader

    return cfg


def capture_final_screenshot(driver, case_id: str, cfg: dict | None = None) -> str | None:
    """
    ✅ 唯一允许截图的入口（给 runner 调用）
    - 不管 PASS/FAIL，用例结束都调用一次
    - case_id 用于生成不冲突的文件名（并发安全）
    """
    try:
        folder = "output/screenshots"
        if cfg and isinstance(cfg, dict):
            folder = (cfg.get("paths") or {}).get("screenshots", folder)
        return take_screenshot(driver, folder, prefix=case_id)
    except Exception:
        return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    yield

    driver = getattr(item.session, "driver", None)
    if not driver:
        return

    screenshot_dir = item.config.getoption("--screenshot-dir", default="output/screenshots")
    path = take_screenshot(driver, screenshot_dir, prefix=getattr(item, "name", "case"))

    # 把截图路径挂到 item 上
    setattr(item, "final_screenshot", path)
