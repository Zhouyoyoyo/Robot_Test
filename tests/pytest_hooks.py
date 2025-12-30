import os
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pytest
import yaml
from _pytest.runner import runtestprotocol

from framework.utils.config_loader import load_config
from framework.utils.excel_loader import load_excel_sheets_kv
from framework.utils.html_report import build_html_report
from framework.utils.logger import get_logger
from framework.utils.mailer import send_report

log = get_logger()


@dataclass
class CaseRecord:
    case_id: str
    sheet: str
    status: str  # PASS / FAIL / ERROR / SKIPPED
    attempt: int
    retried: bool
    start_time: str
    end_time: str
    screenshot: Optional[str]
    error: Optional[str]


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _take_screenshot(driver, out_dir: Path, case_id: str) -> Optional[str]:
    try:
        _ensure_dir(out_dir)
        ts = time.strftime("%Y%m%d_%H%M%S")
        safe_case_id = case_id.replace("/", "_").replace("::", "__")
        filename = f"{safe_case_id}_{ts}.png"
        path = out_dir / filename
        driver.save_screenshot(str(path))
        return str(path)
    except Exception as e:
        log.error(f"[SCREENSHOT] failed: {e}")
        return None


def _zip_dir(src_dir: Path, zip_path: Path) -> str:
    _ensure_dir(zip_path.parent)
    with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(str(src_dir)):
            for f in files:
                fp = Path(root) / f
                rel = fp.relative_to(src_dir)
                z.write(str(fp), str(rel))
    return str(zip_path)


def _normalize_config_paths(cfg: dict) -> dict:
    project_root = Path(cfg.get("_project_root", "."))
    paths = cfg.get("paths", {})
    if isinstance(paths, dict):
        for key, value in list(paths.items()):
            if isinstance(value, str) and value and not Path(value).is_absolute():
                paths[key] = str((project_root / value).resolve())
    cfg["paths"] = paths
    return cfg


def _load_max_reruns() -> int:
    try:
        with open("config/retry_policy.yaml", "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        return 1
    retry_cfg = data.get("retry") or {}
    try:
        return int(retry_cfg.get("max_retry", 1))
    except Exception:
        return 1


def pytest_configure(config):
    config._case_records: Dict[str, CaseRecord] = {}
    config._rerun_count: Dict[str, int] = {}
    cfg = _normalize_config_paths(load_config())
    config._pw_cfg = cfg
    config._pw_max_reruns = _load_max_reruns()


def pytest_runtest_protocol(item, nextitem):
    reruns = item.config._rerun_count.get(item.nodeid, 0)

    item._pw_call_failed_is_assertion = False
    reports = runtestprotocol(item, nextitem=nextitem)

    call_report = next((r for r in reports if r.when == "call"), None)
    should_rerun = (
        call_report is not None
        and call_report.failed
        and getattr(item, "_pw_call_failed_is_assertion", False)
        and reruns < item.config._pw_max_reruns
    )

    if should_rerun:
        item.config._rerun_count[item.nodeid] = reruns + 1
        item._pw_call_failed_is_assertion = False
        runtestprotocol(item, nextitem=nextitem)

    return True


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    sheet_name = None
    try:
        if "sheet_name" in item.funcargs:
            sheet_name = item.funcargs["sheet_name"]
    except Exception:
        sheet_name = None
    if not sheet_name:
        sheet_name = "unknown_sheet"

    if rep.when == "call":
        if rep.failed:
            if call.excinfo and call.excinfo.type is AssertionError:
                item._pw_call_failed_is_assertion = True
                item._pw_outcome = "FAILED"
                item._pw_error_message = str(rep.longrepr)
            else:
                item._pw_outcome = "ERROR"
                item._pw_error_message = str(rep.longrepr)
        elif rep.passed:
            item._pw_outcome = "PASSED"
            item._pw_error_message = None
        elif rep.skipped:
            item._pw_outcome = "SKIPPED"
            item._pw_error_message = str(rep.longrepr)

    if rep.when == "teardown":
        cfg = item.config._pw_cfg
        ss_dir = Path(cfg["paths"]["screenshots"])
        driver = None
        try:
            driver = item.funcargs.get("driver")
        except Exception:
            driver = None

        ss_path = None
        if driver is not None:
            case_id = item.nodeid or sheet_name
            ss_path = _take_screenshot(driver, ss_dir, case_id)

        if not hasattr(item, "_pw_outcome"):
            if rep.failed:
                item._pw_outcome = "ERROR"
                item._pw_error_message = str(rep.longrepr)
            elif rep.skipped:
                item._pw_outcome = "SKIPPED"
                item._pw_error_message = str(rep.longrepr)
            else:
                item._pw_outcome = "PASSED"
                item._pw_error_message = None

        reruns = item.config._rerun_count.get(item.nodeid, 0)
        attempt = 1 + reruns
        status_map = {
            "PASSED": "PASS",
            "FAILED": "FAIL",
            "ERROR": "ERROR",
            "SKIPPED": "SKIP",
        }
        item.config._case_records[item.nodeid] = CaseRecord(
            case_id=item.nodeid,
            sheet=sheet_name,
            status=status_map.get(item._pw_outcome, "ERROR"),
            attempt=attempt,
            retried=reruns > 0,
            start_time="-",
            end_time="-",
            screenshot=ss_path,
            error=item._pw_error_message,
        )


def pytest_sessionfinish(session, exitstatus):
    cfg = session.config._pw_cfg
    records = list(session.config._case_records.values())
    case_params = {}
    try:
        case_params = load_excel_sheets_kv(cfg["paths"]["data"])
    except Exception:
        case_params = {}

    total = len(records)
    passed = sum(1 for r in records if r.status == "PASS")
    failed = sum(1 for r in records if r.status == "FAIL")
    error = sum(1 for r in records if r.status == "ERROR")
    skipped = sum(1 for r in records if r.status == "SKIP")

    out_dir = Path(cfg.get("paths", {}).get("reports", "output/reports"))
    _ensure_dir(out_dir)
    ts = time.strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"report_{ts}.html"

    ss_dir = Path(cfg["paths"]["screenshots"])
    zip_path = out_dir / f"screenshots_{ts}.zip"
    screenshots_zip = None
    if ss_dir.exists():
        screenshots_zip = _zip_dir(ss_dir, zip_path)

    report = build_html_report(records, case_params)
    report_path.write_text(report["html"], encoding="utf-8")

    failed_cases = [r.sheet for r in records if r.status in ("FAIL", "ERROR")]
    pytest_results = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "error": error,
        "skipped": skipped,
        "failed_cases": ", ".join(failed_cases) if failed_cases else "-",
        "report_path": str(report_path),
    }

    send_report(
        pytest_results,
        str(report_path),
        screenshots_zip,
        subject=f"[Automation] Total={total} Pass={passed} Fail={failed} Error={error} Skip={skipped}",
        extra_attachments=[str(report_path)],
    )
