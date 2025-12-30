from openpyxl import load_workbook


def load_excel_kv(path: str, sheet_name: str) -> dict:
    """
    从 Excel 的指定 sheet 中读取数据。
    这是唯一允许的 Excel 读取方式。
    """
    wb = load_workbook(path, data_only=True)

    if sheet_name not in wb.sheetnames:
        raise RuntimeError(
            f"Excel 中不存在名为 [{sheet_name}] 的 sheet"
        )

    ws = wb[sheet_name]
    data = {}

    # 约定：第 1 行是表头，从第 2 行开始
    # A 列是 key，B 列是 value
    for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        key, value = row
        if key is None:
            continue
        data[str(key).strip()] = value

    return data
