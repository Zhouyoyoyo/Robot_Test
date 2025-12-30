from openpyxl import load_workbook


def load_excel_kv(path: str, sheet_name: str) -> dict:
    """
    从 Excel 的指定 sheet 中读取 key-value 数据
    约定：
    - 第 1 行是表头
    - 从第 2 行开始
    - A 列为 key，B 列为 value
    """
    wb = load_workbook(path, data_only=True)

    if sheet_name not in wb.sheetnames:
        raise RuntimeError(
            f"Excel 中不存在名为 [{sheet_name}] 的 sheet"
        )

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
    读取 Excel 中的所有 sheet，返回：
    {
      sheet_name: { key: value, ... },
      ...
    }
    """
    wb = load_workbook(path, data_only=True)
    if not wb.sheetnames:
        raise RuntimeError("Excel 中至少必须存在一个 sheet")

    result = {}
    for name in wb.sheetnames:
        result[name] = load_excel_kv(path, name)

    return result
