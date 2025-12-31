import json
import os
import re
import shutil
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import yaml

from framework.utils.config_loader import load_config
from framework.utils.logger import get_logger
from framework.utils.html_report import build_html_report
from framework.utils.mailer import send_report

log = get_logger()


@dataclass
class AttemptRecord:
    """Author: taobo.zhou
    记录单次测试尝试的结果信息。
    Record result information for a single test attempt.
    """

    nodeid: str
    sheet_name: str
    attempt: int
    outcome: str
    when: str
    longrepr: Optional[str]
    screenshot_path: Optional[str]


@dataclass
class CaseResult:
    """Author: taobo.zhou
    记录最终用例执行结果的汇总信息。
    Record aggregated final case execution information.
    """

    case_id: str
    sheet: str
    status: str
    retried: bool
    attempt: int
    error: Optional[str]
    screenshot: Optional[str]
    nodeid: str
    start_time: str
    end_time: str


def _ensure_dir(p: Path) -> None:
    """Author: taobo.zhou
    创建目录（含父目录），目录已存在时忽略。
    
        p: 需要确保存在的目录路径。
    """

    p.mkdir(parents=True, exist_ok=True)


def _now_ts() -> str:
    """Author: taobo.zhou
    生成当前时间戳字符串。
     无。
    """

    return time.strftime("%Y%m%d_%H%M%S")


def _safe_name(s: str) -> str:
    """Author: taobo.zhou
    将字符串转换为安全的文件名片段。
    
        s: 需要转换的原始字符串。
    """

    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", s)


def _take_screenshot(driver, out_dir: Path, sheet_name: str, attempt: int) -> Optional[str]:
    """Author: taobo.zhou
    保存当前页面截图并返回文件路径。
    
        driver: WebDriver 实例，用于执行截图。
        out_dir: 截图输出目录路径。
        sheet_name: 用例所属 sheet 名称，用于命名。
        attempt: 本次尝试序号，用于命名。
    """

    try:
        _ensure_dir(out_dir)
        ts = _now_ts()
        fn = f"{_safe_name(sheet_name)}__attempt{attempt}__{ts}.png"
        path = out_dir / fn
        driver.save_screenshot(str(path))
        return str(path)
    except Exception as e:
        log.error(f"[SCREENSHOT] failed: {e}")
        return None


def _zip_dir(src_dir: Path, zip_path: Path) -> Optional[str]:
    """Author: taobo.zhou
    将目录内容打包为 zip 文件并返回路径。
    
        src_dir: 需要打包的源目录。
        zip_path: 目标 zip 文件路径。
    """

    if not src_dir.exists():
        return None
    _ensure_dir(zip_path.parent)
    with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(str(src_dir)):
            for f in files:
                fp = Path(root) / f
                rel = fp.relative_to(src_dir)
                z.write(str(fp), str(rel))
    return str(zip_path)


def _get_sheet_name(item) -> str:
    """Author: taobo.zhou
    从 pytest item 中获取 sheet 名称。
    
        item: pytest 用例项对象。
    """

    try:
        if "sheet_name" in item.funcargs:
            return str(item.funcargs["sheet_name"])
    except Exception:
        pass
    return "unknown_sheet"


def _get_attempt(config, nodeid: str) -> int:
    """Author: taobo.zhou
    获取当前用例的尝试序号。
    
        config: pytest 配置对象，包含尝试计数缓存。
        nodeid: 用例唯一标识。
    """

    return int(config._pw_attempts.get(nodeid, 0)) + 1


def _inc_attempt(config, nodeid: str) -> int:
    """Author: taobo.zhou
    递增并返回用例的尝试序号。
    
        config: pytest 配置对象，包含尝试计数缓存。
        nodeid: 用例唯一标识。
    """

    config._pw_attempts[nodeid] = int(config._pw_attempts.get(nodeid, 0)) + 1
    return int(config._pw_attempts[nodeid])


def _is_assertion_failure(call):
    """Author: taobo.zhou
    判断调用结果是否为断言失败。
    
        call: pytest 的 call 对象，包含执行异常信息。
    """

    try:
        excinfo = getattr(call, "excinfo", None)
        if excinfo and isinstance(excinfo.value, AssertionError):
            return True
    except Exception:
        pass

    try:
        text = str(getattr(call, "longrepr", ""))
        if "assert " in text or "AssertionError" in text:
            return True
    except Exception:
        pass

    return False


def _should_retry_error(longrepr: Optional[str], policy: dict) -> bool:
    """Author: taobo.zhou
    根据错误信息与策略判断是否允许重跑。
    
        longrepr: 错误的详细信息字符串。
        policy: 重跑策略配置字典。
    """

    if not longrepr:
        return False

    text = str(longrepr)
    text_lower = text.lower()
    non_retryable = policy.get("non_retryable_keywords") or []
    for kw in non_retryable:
        if kw and str(kw).lower() in text_lower:
            return False

    retryable = policy.get("retryable_keywords") or []
    if not retryable:
        return True

    for kw in retryable:
        if kw and str(kw).lower() in text_lower:
            return True

    return False


def _normalize_status(outc: str) -> str:
    """Author: taobo.zhou
    将 pytest 结果状态标准化为报告状态。
    
        outc: pytest 原始状态字符串。
    """

    mapping = {
        "PASSED": "PASS",
        "FAILED": "FAIL",
        "ERROR": "ERROR",
        "SKIPPED": "SKIP",
    }
    return mapping.get(outc, outc)


def pytest_configure(config):
    """Author: taobo.zhou
    初始化 pytest 配置与重跑策略。
    
        config: pytest 配置对象。
    """

    cfg = load_config()
    config._pw_cfg = cfg
    config._pw_all_attempts: List[AttemptRecord] = []
    config._pw_attempts: Dict[str, int] = {}
    config._pw_final: Dict[str, Tuple[str, int, Optional[str], Optional[str], str]] = {}
    config._pw_rerun_left: Dict[str, int] = {}

    run_dir_opt = config.getoption("--pw-run-dir") or os.environ.get("PW_RUN_DIR")
    if run_dir_opt:
        run_dir = Path(run_dir_opt)
        ss_dir = run_dir / "screenshots"
        rep_dir = run_dir / "reports"
        cfg.setdefault("paths", {})
        cfg["paths"]["screenshots"] = str(ss_dir)
        cfg["paths"]["reports"] = str(rep_dir)
        _ensure_dir(ss_dir)
        _ensure_dir(rep_dir)
        if ss_dir.exists():
            shutil.rmtree(ss_dir)
            ss_dir.mkdir(parents=True, exist_ok=True)

    rp_path = Path("config") / "retry_policy.yaml"
    retry_cfg = {}
    if rp_path.exists():
        try:
            with rp_path.open("r", encoding="utf-8") as f:
                retry_cfg = yaml.safe_load(f) or {}
        except Exception:
            retry_cfg = {}

    retry_section = retry_cfg.get("retry", {}) if isinstance(retry_cfg, dict) else {}
    max_retry = int(retry_section.get("max_retry", 1))
    policy = {
        "max_retry": max_retry,
        "non_retryable_keywords": retry_section.get("non_retryable_keywords") or [],
        "retryable_keywords": retry_section.get("retryable_keywords") or [],
    }
    config._pw_retry_policy = policy
    config._pw_default_reruns = max(0, int(max_retry))

    log.info(f"[PW] default reruns for error failures = {config._pw_default_reruns}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Author: taobo.zhou
    处理用例阶段结果并记录截图与重跑状态。
    
        item: pytest 用例项对象。
        call: pytest 调用信息对象。
    """

    outcome = yield
    rep = outcome.get_result()

    cfg = item.config._pw_cfg
    nodeid = item.nodeid
    sheet_name = getattr(item, "_pw_sheet_name", None) or _get_sheet_name(item)
    attempt = _get_attempt(item.config, nodeid)
    item._pw_sheet_name = sheet_name

    if rep.when == "setup":
        item._pw_error = False
        item._pw_error_longrepr = None
        item._pw_call_outcome = None
        item._pw_call_longrepr = None

    if rep.when == "call":
        if rep.failed:
            if _is_assertion_failure(call):
                item._pw_call_outcome = "FAILED"
                item._pw_call_longrepr = str(rep.longrepr)
            else:
                item._pw_call_outcome = "ERROR"
                item._pw_call_longrepr = str(rep.longrepr)
                item._pw_error = True
                item._pw_error_longrepr = str(rep.longrepr)
        elif rep.passed:
            item._pw_call_outcome = "PASSED"
            item._pw_call_longrepr = None
        elif rep.skipped:
            item._pw_call_outcome = "SKIPPED"
            item._pw_call_longrepr = str(rep.longrepr)

    if rep.when in ("setup", "teardown") and rep.failed:
        item._pw_error = True
        item._pw_error_longrepr = str(rep.longrepr)

    if rep.when == "teardown":
        attempt = _inc_attempt(item.config, nodeid)

        driver = None
        try:
            driver = item.funcargs.get("driver")
        except Exception:
            driver = None

        ss_dir = Path(cfg["paths"]["screenshots"])
        ss_path = None
        if driver is not None:
            ss_path = _take_screenshot(driver, ss_dir, sheet_name, attempt)

        if getattr(item, "_pw_error", False):
            outc = "ERROR"
            lr = getattr(item, "_pw_error_longrepr", None)
        else:
            call_outc = getattr(item, "_pw_call_outcome", None)
            if call_outc == "FAILED":
                outc = "FAILED"
                lr = getattr(item, "_pw_call_longrepr", None)
            elif call_outc == "PASSED":
                outc = "PASSED"
                lr = None
            elif call_outc == "SKIPPED":
                outc = "SKIPPED"
                lr = getattr(item, "_pw_call_longrepr", None)
            else:
                outc = "PASSED"
                lr = None

        ar = AttemptRecord(
            nodeid=nodeid,
            sheet_name=sheet_name,
            attempt=attempt,
            outcome=outc,
            when="call",
            longrepr=lr,
            screenshot_path=ss_path,
        )
        item.config._pw_all_attempts.append(ar)
        item.config._pw_final[nodeid] = (outc, attempt, lr, ss_path, sheet_name)

        if outc == "ERROR":
            left = item.config._pw_rerun_left.get(nodeid)
            if left is None:
                policy = item.config._pw_retry_policy
                if _should_retry_error(lr, policy):
                    item.config._pw_rerun_left[nodeid] = int(item.config._pw_default_reruns)
                else:
                    item.config._pw_rerun_left[nodeid] = 0
        else:
            item.config._pw_rerun_left[nodeid] = 0


def pytest_runtestloop(session):
    """Author: taobo.zhou
    实现 pytest 用例循环执行与 ERROR 重跑逻辑。
    
        session: pytest 会话对象。
    """

    config = session.config
    items = list(session.items)

    i = 0
    while i < len(items):
        item = items[i]
        item.config.hook.pytest_runtest_protocol(item=item, nextitem=items[i + 1] if i + 1 < len(items) else None)

        nodeid = item.nodeid
        final = config._pw_final.get(nodeid)
        if not final:
            i += 1
            continue

        outc, attempt, lr, ss, sheet = final
        left = int(config._pw_rerun_left.get(nodeid, 0))

        if outc == "ERROR" and left > 0:
            config._pw_rerun_left[nodeid] = left - 1
            log.warning(
                "[PW][RERUN] nodeid=%s sheet=%s attempt=%s -> rerun, left=%s",
                nodeid,
                sheet,
                attempt,
                left - 1,
            )
            continue

        i += 1

    return True


def pytest_sessionfinish(session, exitstatus):
    """Author: taobo.zhou
    汇总最终态结果，生成报告并发送邮件。
    
        session: pytest 会话对象。
        exitstatus: pytest 退出状态码。
    """

    cfg = session.config._pw_cfg
    out_dir = Path(cfg.get("paths", {}).get("reports", "output/reports"))
    _ensure_dir(out_dir)

    ts = _now_ts()
    report_path = out_dir / f"report_{ts}.html"

    results: List[CaseResult] = []
    case_params: Dict[str, Dict[str, str]] = {}
    results_payload: List[Dict[str, object]] = []

    for nodeid, (outc, attempt, lr, ss, sheet_name) in session.config._pw_final.items():
        status = _normalize_status(outc)
        results.append(CaseResult(
            case_id=sheet_name,
            sheet=sheet_name,
            status=status,
            retried=(attempt > 1),
            attempt=attempt,
            error=lr,
            screenshot=ss,
            nodeid=nodeid,
            start_time="-",
            end_time="-",
        ))
        results_payload.append({
            "case_id": sheet_name,
            "sheet": sheet_name,
            "status": status,
            "retried": attempt > 1,
            "attempt": attempt,
            "error": lr,
            "screenshot": ss,
            "nodeid": nodeid,
            "start_time": "-",
            "end_time": "-",
        })
        case_params[sheet_name] = {
            "sheet_name": sheet_name,
        }

    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    error = sum(1 for r in results if r.status == "ERROR")
    skipped = sum(1 for r in results if r.status == "SKIP")

    results_json = {
        "sheet": session.config.getoption("--pw-sheet") or "unknown",
        "counts": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
        },
        "results": results_payload,
        "case_params": case_params,
    }
    results_path = out_dir / "results.json"
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)

    worker_mode = bool(session.config.getoption("--pw-worker")) or os.environ.get("PW_WORKER") == "1"
    if worker_mode:
        log.info("[PW][WORKER] results written: %s", results_path)
        return

    report_info = build_html_report(results, case_params)
    html = report_info.get("html") or report_info.get("html_content") or report_info.get("content")
    if not html:
        html = (
            f"<html><body><h2>Report</h2><p>Total={total} Pass={passed} Fail={failed} "
            f"Error={error} Skip={skipped}</p></body></html>"
        )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    ss_dir = Path(cfg["paths"]["screenshots"])
    zip_path = out_dir / f"screenshots_{ts}.zip"
    screenshot_zip = _zip_dir(ss_dir, zip_path)

    subject = f"Robot 自动化测试报告 | Total={total} Pass={passed} Fail={failed} Error={error} Skip={skipped}"
    ok = send_report(
        pytest_results={
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "details": results_payload,
        },
        html_report=str(report_path),
        screenshot_zip=screenshot_zip,
        subject=subject,
        extra_attachments=None,
    )
    log.info(f"[PW][MAIL] sent={ok} report={report_path} zip={screenshot_zip}")
