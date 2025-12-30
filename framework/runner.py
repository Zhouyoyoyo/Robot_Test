from __future__ import annotations
from tests.conftest import capture_final_screenshot
from framework.utils.html_report import build_html_report

"""项目启动入口（run.py 调用）"""

import os
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from framework.driver.driver_factory import create_driver
from framework.utils.config_loader import load_config, PROJECT_ROOT
from framework.utils.excel_loader import load_excel_sheets_kv
from framework.utils.locator_loader import LocatorLoader
from framework.utils.logger import get_logger, set_current_test
from framework.utils.mailer import send_html_mail
from pages.login_page import LoginPage
from pages.software_container_page import SoftwareContainerPage


# =========================================================
# CaseResult（你原来的定义，保持，只确保构造时字段齐全）
# =========================================================
@dataclass
class CaseResult:
    case_id: str
    sheet: str
    iteration: int
    status: str  # PASS / FAIL
    seconds: float
    start_time: str
    end_time: str
    error: str | None = None
    screenshot: str | None = None


def _init_config() -> Dict[str, Any]:
    cfg = load_config()

    project_root = Path(cfg.get("_project_root", PROJECT_ROOT))
    if "paths" in cfg and isinstance(cfg["paths"], dict):
        for k, v in list(cfg["paths"].items()):
            if isinstance(v, str) and v and not Path(v).is_absolute():
                cfg["paths"][k] = str((project_root / v).resolve())

    get_logger()

    locator_path = cfg["paths"]["locator"]
    loader = LocatorLoader(locator_path)
    loader.validate_all()
    cfg["locator_loader"] = loader

    return cfg


def _get_case_url(cfg: Dict[str, Any], sheet_name: str, data: Dict[str, Any]) -> str:
    """根据 sheet 名从 config.yaml 取 URL。"""
    project = cfg.get("project", {}) or {}

    key = f"{sheet_name}"
    if key in project and project[key]:
        return str(project[key])

    if data.get("login.url"):
        return str(data["login.url"])

    raise KeyError(
        f"URL not found: config.yaml project.{key} or sheet[{sheet_name}].login.url"
    )


def _get_repeat_times(data: Dict[str, Any]) -> int:
    for k in ("run.times", "repeat", "times"):
        if k in data and data[k] is not None and str(data[k]).strip() != "":
            try:
                return max(1, int(float(data[k])))
            except Exception:
                return 1
    return 1


def _apply_driver_timeouts(driver, cfg: Dict[str, Any]) -> None:
    sel = cfg.get("selenium", {}) or {}
    try:
        page_load = float(sel.get("page_load_timeout", 60))
        driver.set_page_load_timeout(page_load)
    except Exception:
        pass


def _run_one_case(cfg: Dict[str, Any], sheet: str, iteration: int, data: Dict[str, Any]) -> CaseResult:
    case_id = f"{sheet}__{iteration:02d}"
    set_current_test(case_id)
    log = get_logger()

    start_dt = datetime.now()
    start_ts = time.time()

    driver = None
    screenshot_path = None
    status = "FAIL"
    err = None

    try:
        driver = create_driver(cfg["project"]["browser"])
        _apply_driver_timeouts(driver, cfg)

        username = data["login.username"]
        password = data["login.password"]
        url = _get_case_url(cfg, sheet, data)

        page_login = LoginPage(driver, cfg["locator_loader"])
        page_login.open(url)
        page_login.wait_page_ready()
        page_login.wait_visible("next_button")
        page_login.login(username, password)

        page = SoftwareContainerPage(driver, cfg["locator_loader"])
        page.create_version(
            data["version"],
            data["semantic_version"],
            data["general_setting"],
            data["software_part_number"],
            data["software_YMP_version"],
            data["dependencies"],
            data["file_upload_ODX_F"],
            data["file_upload_flashware"],
        )

        status = "PASS"

    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        log.error(f"[CASE_DONE] {case_id} FAIL err={err}")
        log.error(traceback.format_exc())

    finally:
        # ✅ 用例结束必截图：唯一入口在 conftest.py
        if driver is not None:
            screenshot_path = capture_final_screenshot(driver, case_id, cfg)

        end_dt = datetime.now()
        seconds = time.time() - start_ts

        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass
        set_current_test("-")

    return CaseResult(
        case_id=case_id,
        sheet=sheet,
        iteration=iteration,
        status=status,
        seconds=seconds,
        start_time=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        error=err,
        screenshot=screenshot_path,
    )


def _write_summary(results: List[CaseResult], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"results_{ts}.csv")

    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "sheet", "iteration", "status", "seconds", "error", "screenshot"])
        for r in results:
            w.writerow([
                r.case_id, r.sheet, r.iteration, r.status,
                f"{r.seconds:.2f}", r.error or "", r.screenshot or ""
            ])
    return path


def run_tests() -> None:
    cfg = _init_config()
    log = get_logger()

    data_path = cfg["paths"]["data"]
    sheets = load_excel_sheets_kv(data_path)

    tasks: List[Tuple[str, int, Dict[str, Any]]] = []
    for sheet_name, data in sheets.items():
        repeat = _get_repeat_times(data)
        for i in range(1, repeat + 1):
            tasks.append((sheet_name, i, data))

    if not tasks:
        raise RuntimeError(f"No test cases found in excel: {data_path}")

    runner_cfg = cfg.get("runner", {}) or {}
    max_workers = int(runner_cfg.get("max_workers", 4))
    max_workers = max(1, min(max_workers, len(tasks)))

    log.info(f"[RUNNER] excel={data_path} sheets={len(sheets)} tasks={len(tasks)} workers={max_workers}")

    results: List[CaseResult] = []
    start_all = time.time()

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="case") as pool:
        future_map = {
            pool.submit(_run_one_case, cfg, sheet, it, data): (sheet, it)
            for (sheet, it, data) in tasks
        }

        for fut in as_completed(future_map):
            results.append(fut.result())

    total_seconds = time.time() - start_all
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status != "PASS")

    log.info("=" * 80)
    log.info(f"[SUMMARY] total={len(results)} pass={passed} fail={failed} seconds={total_seconds:.2f}")
    for r in results:
        if r.status != "PASS":
            log.error(f"[FAIL] {r.case_id} err={r.error} screenshot={r.screenshot}")
    log.info("=" * 80)

    out_dir = str((Path(PROJECT_ROOT) / "output").resolve())
    summary_path = _write_summary(results, out_dir)
    log.info(f"[SUMMARY_FILE] {summary_path}")

    # 邮件通知（HTML 正文）
    try:
        report = build_html_report(results, case_params=sheets)

        send_html_mail(
            subject="Robot BTV 自动化测试报告",
            html_body=report["html"],
            inline_images=report["inline_images"],
            attachments=report["attachments"],
        )
    except Exception as e:
        log.warning(f"Send mail failed: {e}")
