"""运行入口模块。

Run entry module.

Author: taobo.zhou
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest

from framework.utils.pytest_args import build_pytest_args
from framework.utils.retry_policy import RetryPolicy
from framework.utils.retry_utils import parse_failed_cases_with_retry_flag


OUTPUT_DIR = Path("output")


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


def write_simple_html_report(
    report_path: Path,
    retryable_failures: list[str],
    non_retryable_failures: list[str],
) -> None:
    def render_list(items: list[str]) -> str:
        if not items:
            return "<p class='muted'>None</p>"
        rows = "".join(f"<li>{item}</li>" for item in items)
        return f"<ul>{rows}</ul>"

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: Arial, sans-serif; font-size: 13px; color: #222; }}
section {{ margin-bottom: 16px; }}
.muted {{ color: #777; }}
</style>
</head>
<body>
<h2>Retry Report</h2>

<section>
  <h3>Retryable Failures</h3>
  {render_list(retryable_failures)}
</section>

<section>
  <h3>Non-Retryable Failures (Assertion / Logic)</h3>
  {render_list(non_retryable_failures)}
</section>
</body>
</html>"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html, encoding="utf-8")


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

    write_simple_html_report(
        OUTPUT_DIR / "retry_report.html",
        retryable_failures=retryable_nodeids,
        non_retryable_failures=non_retryable_nodeids,
    )

    return code


if __name__ == "__main__":
    raise SystemExit(main())
