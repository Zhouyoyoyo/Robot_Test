"""运行入口模块。

Run entry module.

Author: taobo.zhou
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

import pytest

from framework.utils.config_loader import load_config
from framework.utils.excel_loader import load_excel_sheets_kv
from framework.utils.html_report import build_html_report
from framework.utils.mailer import send_report
from framework.utils.pytest_args import build_pytest_args
from framework.utils.retry_policy import RetryPolicy
from framework.utils.retry_utils import parse_failed_cases_with_retry_flag


OUTPUT_DIR = Path("output")
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"


@dataclass
class CaseResult:
    case_id: str
    status: str
    error: str
    seconds: float
    start_time: str
    end_time: str
    screenshot: str | None
    attempt: int
    retried: bool
    sheet: str


def _load_case_params(cfg: dict) -> dict[str, dict]:
    data_path = (cfg.get("paths") or {}).get("data")
    if not data_path:
        return {"default": {}}
    try:
        params = load_excel_sheets_kv(data_path)
    except Exception:
        return {"default": {}}
    return params or {"default": {}}


def _build_nodeid(case: ET.Element) -> str:
    name = case.attrib.get("name", "")
    file_attr = case.attrib.get("file")
    if file_attr:
        return f"{file_attr}::{name}"

    classname = case.attrib.get("classname", "")
    if classname:
        module_path = classname.replace(".", "/")
        if not module_path.endswith(".py"):
            module_path = f"{module_path}.py"
        return f"{module_path}::{name}"

    return name


def _screenshot_path(nodeid: str) -> str | None:
    if not nodeid:
        return None
    filename = nodeid.replace("/", "_").replace("::", "__")
    return str(SCREENSHOTS_DIR / f"{filename}.png")


def _parse_pytest_summary(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    try:
        tree = ET.parse(path)
    except Exception:
        return None

    root = tree.getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return None

    summary: dict[str, str] = {}
    for key in ("tests", "failures", "errors", "skipped", "time"):
        value = suite.attrib.get(key)
        if value is not None:
            summary[key] = value
    return summary or None


def _parse_case_results(
    path: Path,
    attempt: int,
    case_params: dict[str, dict],
) -> list[CaseResult]:
    if not path.exists():
        return []
    try:
        tree = ET.parse(path)
    except Exception:
        return []

    sheet_name = next(iter(case_params.keys()), "default")
    results: list[CaseResult] = []

    for case in tree.getroot().findall(".//testcase"):
        nodeid = _build_nodeid(case)
        status = "PASS"
        error = ""

        failure = case.find("failure")
        error_node = case.find("error")
        skipped_node = case.find("skipped")

        if failure is not None or error_node is not None:
            status = "FAIL"
            detail = failure if failure is not None else error_node
            error = (detail.text or detail.attrib.get("message", "")).strip()
        elif skipped_node is not None:
            status = "SKIP"

        seconds = float(case.attrib.get("time", "0") or 0)

        results.append(
            CaseResult(
                case_id=nodeid or case.attrib.get("name", "-"),
                status=status,
                error=error,
                seconds=seconds,
                start_time="-",
                end_time="-",
                screenshot=_screenshot_path(nodeid),
                attempt=attempt,
                retried=attempt > 1,
                sheet=sheet_name,
            )
        )

    return results


def _strip_junit_args(args: list[str]) -> list[str]:
    cleaned: list[str] = []
    skip_next = False

    for arg in args:
        if skip_next:
            skip_next = False
            continue

        if arg == "--junitxml":
            skip_next = True
            continue

        if arg.startswith("--junitxml="):
            continue

        cleaned.append(arg)

    return cleaned


def junit_path(attempt: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"junit_attempt_{attempt}.xml"


def finalize_junit(final_attempt: int) -> None:
    """Publish final junit result to output/junit.xml for a single source of truth."""
    src = junit_path(final_attempt)
    dst = OUTPUT_DIR / "junit.xml"
    try:
        if src.exists():
            shutil.copy2(src, dst)
    except Exception:
        pass


def _run_round(
    attempt: int,
    base_args: list[str],
    only_nodeids: Iterable[str],
) -> int:
    args = list(base_args)
    args.extend(["--junitxml", str(junit_path(attempt))])
    if only_nodeids:
        args.extend(list(only_nodeids))
    return pytest.main(args)


def main() -> int:
    base_args = _strip_junit_args(build_pytest_args())
    max_retry = RetryPolicy.max_retry()

    attempt = 1
    code = _run_round(attempt=attempt, base_args=base_args, only_nodeids=[])

    failed_cases = parse_failed_cases_with_retry_flag(junit_path(attempt))
    retryable_nodeids = [n for n, can_retry in failed_cases if can_retry]
    non_retryable_nodeids = [n for n, can_retry in failed_cases if not can_retry]

    retry_count = 0
    while retry_count < max_retry and code != 0 and retryable_nodeids:
        retry_count += 1
        attempt = 1 + retry_count
        code = _run_round(
            attempt=attempt,
            base_args=base_args,
            only_nodeids=retryable_nodeids,
        )

        failed_cases = parse_failed_cases_with_retry_flag(junit_path(attempt))
        retryable_nodeids = [n for n, can_retry in failed_cases if can_retry]
        non_retryable_nodeids = [n for n, can_retry in failed_cases if not can_retry]

    finalize_junit(attempt)

    try:
        cfg = load_config()
        mail_cfg = cfg.get("mail", {}) or {}
        if mail_cfg.get("enable", False):
            case_params = _load_case_params(cfg)
            results = _parse_case_results(junit_path(attempt), attempt, case_params)
            report = build_html_report(results, case_params)
            send_report(
                _parse_pytest_summary(junit_path(attempt)),
                report["html"],
                None,
                subject=mail_cfg.get("subject", "自动化测试报告"),
                extra_attachments=report.get("attachments", []),
            )
    except Exception as e:
        print(f"[MAIL][ERROR] {e}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
