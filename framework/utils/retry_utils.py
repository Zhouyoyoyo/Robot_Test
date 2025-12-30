"""Retry-related utility helpers."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from framework.utils.retry_policy import RetryPolicy


def parse_failed_cases_with_retry_flag(junit_xml: Path) -> list[tuple[str, bool]]:
    """
    Return:
      [
        (nodeid, is_retryable),
        ...
      ]
    """
    if not junit_xml.exists():
        return []

    try:
        tree = ET.parse(str(junit_xml))
        root = tree.getroot()
    except Exception:
        return []

    results: list[tuple[str, bool]] = []

    for tc in root.iter("testcase"):
        failure_node = None
        for child in list(tc):
            tag = (child.tag or "").lower()
            if tag in ("failure", "error"):
                failure_node = child
                break

        if failure_node is None:
            continue

        classname = tc.attrib.get("classname", "").strip()
        name = tc.attrib.get("name", "").strip()
        if not classname or not name:
            continue

        path = classname.replace(".", "/") + ".py"
        nodeid = f"{path}::{name}"

        failure_text = (
            (failure_node.attrib.get("message") or "")
            + "\n"
            + (failure_node.text or "")
        )

        retryable = RetryPolicy.is_retryable(failure_text)
        results.append((nodeid, retryable))

    return results
