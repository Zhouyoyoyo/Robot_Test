"""
Retry policy (YAML driven).

This module loads retry rules from config/retry_policy.yaml
and determines whether a failure is retryable at runtime.
"""

from __future__ import annotations

from pathlib import Path

import yaml


class RetryPolicy:
    _loaded = False
    _max_retry: int = 1
    _retryable_keywords: list[str] = []
    _non_retryable_keywords: list[str] = []

    @classmethod
    def _load(cls) -> None:
        if cls._loaded:
            return

        cfg_path = Path("config/retry_policy.yaml")
        if not cfg_path.exists():
            raise RuntimeError(
                "retry_policy.yaml not found in config/ directory"
            )

        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        retry_cfg = data.get("retry", {})

        cls._max_retry = int(retry_cfg.get("max_retry", 1))
        cls._retryable_keywords = list(retry_cfg.get("retryable_keywords", []))
        cls._non_retryable_keywords = list(retry_cfg.get("non_retryable_keywords", []))

        cls._loaded = True

    @classmethod
    def max_retry(cls) -> int:
        cls._load()
        return cls._max_retry

    @classmethod
    def is_retryable(cls, failure_text: str) -> bool:
        cls._load()

        if not failure_text:
            return False

        text = failure_text.lower()

        # Safety guard: if retryable keywords is empty, never retry
        if not cls._retryable_keywords:
            return False

        # 1️⃣ 一票否决（断言 / 逻辑失败）
        for k in cls._non_retryable_keywords:
            if k.lower() in text:
                return False

        # 2️⃣ 命中白名单 → 可重跑
        for k in cls._retryable_keywords:
            if k.lower() in text:
                return True

        # 3️⃣ 默认：不重跑
        return False
