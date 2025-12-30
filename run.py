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

    return code


if __name__ == "__main__":
    raise SystemExit(main())
