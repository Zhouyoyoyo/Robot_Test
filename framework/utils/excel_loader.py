"""Excel 数据加载模块。

Excel data loader module.

作者: taobo.zhou
Author: taobo.zhou
"""

from __future__ import annotations

from typing import Dict, Any

from openpyxl import load_workbook


def _sheet_to_kv(ws) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        key, value = row
        if key is None:
            continue
        k = str(key).strip()
        if not k:
            continue
        data[k] = value
    return data


def load_excel_kv(path: str) -> Dict[str, Any]:
    wb = load_workbook(path)
    ws = wb.active
    return _sheet_to_kv(ws)


def load_excel_sheets_kv(path: str) -> Dict[str, Dict[str, Any]]:
    wb = load_workbook(path)
    out: Dict[str, Dict[str, Any]] = {}
    for name in wb.sheetnames:
        ws = wb[name]
        out[name] = _sheet_to_kv(ws)
    return out
