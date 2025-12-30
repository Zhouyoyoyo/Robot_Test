from openpyxl import load_workbook


def load_excel_kv(path: str, sheet_name: str) -> dict:
    """
    从 Excel 的指定 sheet 中读取 key-value 数据。
    约定：
    - 第 1 行是表头
    - 从第 2 行开始读
    - A 列 key，B 列 value
    """
    wb = load_workbook(path, data_only=True)

    if sheet_name not in wb.sheetnames:
        raise RuntimeError(f"Excel 中不存在名为 [{sheet_name}] 的 sheet")

    ws = wb[sheet_name]
    data = {}

    for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        key, value = row
        if key is None:
            continue
        data[str(key).strip()] = value

    return data


def load_excel_sheets_kv(path: str) -> dict:
    """
    读取 Excel 的所有 sheet，返回：
    {
      "1": { ...sheet1 的 kv... },
      "2": { ...sheet2 的 kv... }
    }

    注意：严禁读取 active sheet。必须逐个按 sheetname 读取。
    """
    wb = load_workbook(path, data_only=True)
    out = {}

    for name in wb.sheetnames:
        out[name] = load_excel_kv(path, name)

    return out
