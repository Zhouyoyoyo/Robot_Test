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
    nodeid: str
    sheet_name: str
    attempt: int  # 1..N
    outcome: str  # PASSED / FAILED / ERROR / SKIPPED
    when: str     # call/setup/teardown (最终以 call 为准)
    longrepr: Optional[str]
    screenshot_path: Optional[str]


@dataclass
class CaseResult:
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
    p.mkdir(parents=True, exist_ok=True)


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _safe_name(s: str) -> str:
    # 用于文件名：替换非法字符
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", s)


def _take_screenshot(driver, out_dir: Path, sheet_name: str, attempt: int) -> Optional[str]:
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
    try:
        if "sheet_name" in item.funcargs:
            return str(item.funcargs["sheet_name"])
    except Exception:
        pass
    return "unknown_sheet"


def _get_attempt(config, nodeid: str) -> int:
    # attempt = 已执行次数 + 1
    return int(config._pw_attempts.get(nodeid, 0)) + 1


def _inc_attempt(config, nodeid: str) -> int:
    config._pw_attempts[nodeid] = int(config._pw_attempts.get(nodeid, 0)) + 1
    return int(config._pw_attempts[nodeid])


def _is_assertion_failure(call):
    """
    判断是否为“验证失败（AssertionError）”
    规则：
    1️⃣ 优先通过异常类型判断（最可靠）
    2️⃣ 若拿不到 excinfo，再退化为字符串兜底
    """
    try:
        excinfo = getattr(call, "excinfo", None)
        if excinfo and isinstance(excinfo.value, AssertionError):
            return True
    except Exception:
        pass

    # 兜底：pytest 断言重写有时不直接暴露 AssertionError
    try:
        text = str(getattr(call, "longrepr", ""))
        if "assert " in text or "AssertionError" in text:
            return True
    except Exception:
        pass

    return False


def _should_retry_error(longrepr: Optional[str], policy: dict) -> bool:
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
    mapping = {
        "PASSED": "PASS",
        "FAILED": "FAIL",
        "ERROR": "ERROR",
        "SKIPPED": "SKIP",
    }
    return mapping.get(outc, outc)


def pytest_addoption(parser):
    parser.addoption("--pw-sheet", action="store", default=None, help="仅运行指定 sheet")
    parser.addoption("--pw-worker", action="store_true", help="标记当前进程为 worker")
    parser.addoption("--pw-run-dir", action="store", default=None, help="指定当前进程输出目录")


def pytest_configure(config):
    cfg = load_config()
    config._pw_cfg = cfg

    # 记录所有尝试（含重跑）
    config._pw_all_attempts: List[AttemptRecord] = []

    # nodeid -> 已尝试次数（用于 attempt 序号）
    config._pw_attempts: Dict[str, int] = {}

    # nodeid -> 最终态（用于收敛）
    # value: (outcome, attempt, longrepr, screenshot_path, sheet_name)
    config._pw_final: Dict[str, Tuple[str, int, Optional[str], Optional[str], str]] = {}

    # nodeid -> 是否允许继续重跑（只允许 ERROR）
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
    """
    1) 记录 call 阶段 outcome（FAILED=验证失败，ERROR=异常）
    2) teardown 阶段强制截图（无论PASS/FAIL/ERROR）
    3) 记录 attempt 记录
    """
    outcome = yield
    rep = outcome.get_result()

    cfg = item.config._pw_cfg
    nodeid = item.nodeid
    sheet_name = getattr(item, "_pw_sheet_name", None) or _get_sheet_name(item)

    # 尝试序号（每次真正执行一次用例，attempt递增）
    # 用 teardown 截图时能拿到正确 attempt，因此这里不增，只读取当前值+1作为本轮
    attempt = _get_attempt(item.config, nodeid)

    # 保存 sheet_name 到 item 供后续使用
    item._pw_sheet_name = sheet_name

    # setup 阶段：重置状态，避免重跑时污染
    if rep.when == "setup":
        item._pw_error = False
        item._pw_error_longrepr = None
        item._pw_call_outcome = None
        item._pw_call_longrepr = None

    # call 阶段：确定验证失败/通过/跳过
    if rep.when == "call":
        if rep.failed:
            if _is_assertion_failure(call):
                item._pw_call_outcome = "FAILED"  # 验证失败（assert）
                item._pw_call_longrepr = str(rep.longrepr)
            else:
                item._pw_call_outcome = "ERROR"  # 非验证失败（异常）
                item._pw_call_longrepr = str(rep.longrepr)
                item._pw_error = True
                item._pw_error_longrepr = str(rep.longrepr)
        elif rep.passed:
            item._pw_call_outcome = "PASSED"
            item._pw_call_longrepr = None
        elif rep.skipped:
            item._pw_call_outcome = "SKIPPED"
            item._pw_call_longrepr = str(rep.longrepr)

    # setup/teardown 的 rep.failed 属于 ERROR 类（不重跑）
    if rep.when in ("setup", "teardown") and rep.failed:
        item._pw_error = True
        item._pw_error_longrepr = str(rep.longrepr)

    # teardown 阶段：截图 + 落地本次 attempt 记录
    if rep.when == "teardown":
        # 本轮 attempt 正式计数+1
        attempt = _inc_attempt(item.config, nodeid)

        # 拿 driver
        driver = None
        try:
            driver = item.funcargs.get("driver")
        except Exception:
            driver = None

        ss_dir = Path(cfg["paths"]["screenshots"])
        ss_path = None
        if driver is not None:
            ss_path = _take_screenshot(driver, ss_dir, sheet_name, attempt)

        # 计算本轮最终 outcome：优先 ERROR，其次 FAILED，再 PASSED，最后 SKIPPED
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

        # 更新最终态（收敛规则）：
        # - 若本轮 PASSED：最终态=PASSED（覆盖之前失败）
        # - 若本轮 FAILED/ERROR：最终态=该状态（若之后仍有重跑，最终会被后续覆盖）
        item.config._pw_final[nodeid] = (outc, attempt, lr, ss_path, sheet_name)

        # 若本轮为 ERROR（非断言异常），按策略初始化/更新可重跑次数
        if outc == "ERROR":
            left = item.config._pw_rerun_left.get(nodeid)
            if left is None:
                policy = item.config._pw_retry_policy
                if _should_retry_error(lr, policy):
                    item.config._pw_rerun_left[nodeid] = int(item.config._pw_default_reruns)
                else:
                    item.config._pw_rerun_left[nodeid] = 0
        else:
            # PASSED/FAILED/SKIPPED：不需要重跑
            item.config._pw_rerun_left[nodeid] = 0


def pytest_runtestloop(session):
    """
    实现：仅对 ERROR（非断言异常）重跑，FAILED 不重跑。
    方法：在同一进程中循环执行 items；若某 item ERROR 且仍有 rerun_left，则再次执行它。
    注意：再次执行使用同一个 item，因此天然绑定 sheet_name / data / url（满足“失败重跑用原数据”）。
    """
    config = session.config
    items = list(session.items)

    i = 0
    while i < len(items):
        item = items[i]
        # 运行一次 item（标准流程）
        item.config.hook.pytest_runtest_protocol(item=item, nextitem=items[i + 1] if i + 1 < len(items) else None)

        nodeid = item.nodeid
        final = config._pw_final.get(nodeid)
        if not final:
            i += 1
            continue

        outc, attempt, lr, ss, sheet = final
        left = int(config._pw_rerun_left.get(nodeid, 0))

        # 仅 ERROR 才重跑；FAILED 不重跑；PASSED 不重跑
        if outc == "ERROR" and left > 0:
            config._pw_rerun_left[nodeid] = left - 1
            log.warning(
                "[PW][RERUN] nodeid=%s sheet=%s attempt=%s -> rerun, left=%s",
                nodeid,
                sheet,
                attempt,
                left - 1,
            )
            # 不推进 i，立即再次执行同一个 item
            continue

        # 不需要重跑则推进
        i += 1

    # 退出码交给 pytest 自己处理（此处返回 None 表示已执行完 loop）
    return True


def pytest_sessionfinish(session, exitstatus):
    """
    session结束：使用“最终态”生成报告并发邮件，截图打包zip。
    关键：报告/邮件只看最终态（重跑成功则PASS）。
    """
    cfg = session.config._pw_cfg
    out_dir = Path(cfg.get("paths", {}).get("reports", "output/reports"))
    _ensure_dir(out_dir)

    ts = _now_ts()
    report_path = out_dir / f"report_{ts}.html"

    # 1) 构造最终 results（兼容你现有 build_html_report 所需结构）
    # 你现有 html_report.build_html_report(results, case_params)
    # 其中 results 期望是一个列表，每个元素至少包含：
    # - name / nodeid / outcome / error 等（你现有实现会读取哪些字段）
    # 为避免破坏，你这里按最稳的通用字段输出：
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
        # case_params 用于报告里展示参数；至少放 sheet_name 与 url 映射键
        case_params[sheet_name] = {
            "sheet_name": sheet_name,
        }

    # 统计
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

    # 2) 生成 HTML 报告（复用现有实现）
    report_info = build_html_report(results, case_params)
    # 你的 build_html_report 返回 dict，里面可能有 html_content / path；为了稳定，始终写入 report_path
    html = report_info.get("html") or report_info.get("html_content") or report_info.get("content")
    if not html:
        # 若现有实现直接在内部写文件，则这里兜底写一个最简单HTML，避免空报告
        html = f"<html><body><h2>Report</h2><p>Total={total} Pass={passed} Fail={failed} Error={error} Skip={skipped}</p></body></html>"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 3) 打包截图 zip（只打包当前目录下已有文件；若你希望仅本次运行文件，可在后续增强为清理策略）
    ss_dir = Path(cfg["paths"]["screenshots"])
    zip_path = out_dir / f"screenshots_{ts}.zip"
    screenshot_zip = _zip_dir(ss_dir, zip_path)

    # 4) 发邮件（复用现有 send_report）
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
