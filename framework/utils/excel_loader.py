"""
Excel 数据加载工具

1) data/testdata.xlsx 中 **每个 sheet 表示一个可独立执行的测试用例**。
2) sheet 内数据采用 Key/Value 的两列结构：
   - A 列：key
   - B 列：value
   - 从第 2 行开始读取（第 1 行通常是表头）
"""

from __future__ import annotations

from typing import Dict, Any

from openpyxl import load_workbook


def _sheet_to_kv(ws) -> Dict[str, Any]:
    """把一个 sheet 转成 dict。

    读取规则：
      - 从第 2 行开始
      - 只读取 A/B 两列
      - 忽略 key 为空的行
    """
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
    """读取 Excel 活动 sheet 的 KV（旧接口，保持不破坏现有代码）。"""
    wb = load_workbook(path)
    ws = wb.active
    return _sheet_to_kv(ws)


def load_excel_sheets_kv(path: str) -> Dict[str, Dict[str, Any]]:
    """读取 Excel 中所有 sheet 的 KV。

    Returns
    -------
    dict[sheet_name, dict[key, value]]
    """
    wb = load_workbook(path)
    out: Dict[str, Dict[str, Any]] = {}
    for name in wb.sheetnames:
        ws = wb[name]
        out[name] = _sheet_to_kv(ws)
    return out
