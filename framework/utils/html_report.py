"""HTML 报告构建模块。

HTML report builder module.

作者: taobo.zhou
Author: taobo.zhou
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import List, Dict, Any
import uuid
import os


def build_html_report(
    results: List[Any],
    case_params: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    inline_images: Dict[str, str] = {}
    attachments: List[str] = []

    def new_cid() -> str:
        return f"img_{uuid.uuid4().hex}@report"

    rows_html = []

    for r in results:
        params = case_params.get(r.sheet, {})
        params_main_keys = []
        if "login.username" in params:
            params_main_keys.append("login.username")
        if "version" in params:
            params_main_keys.append("version")
        if not params_main_keys:
            params_main_keys = list(params.keys())[:2]

        params_main = " / ".join(
            f"{k}={params.get(k)}" for k in params_main_keys
        ) or "-"

        params_kv_html = "".join(
            f"<div class='k'>{escape(str(k))}</div>"
            f"<div class='v'>{escape(str(v))}</div>"
            for k, v in params.items()
        )

        screenshots_html = ""
        if r.screenshot and os.path.exists(r.screenshot):
            cid = f"img_{uuid.uuid4().hex}@report"
            inline_images[cid] = r.screenshot
            attachments.append(r.screenshot)

            name = os.path.basename(r.screenshot)
            screenshots_html = f"<div>📷 <a href='cid:{cid}'>{escape(name)}</a></div>"
        else:
            screenshots_html = "<div class='muted'>⚠ 截图缺失</div>"

        error_html = (
            f"<pre>{escape(r.error)}</pre>"
            if r.error
            else "<div class='muted'>无失败日志</div>"
        )

        rows_html.append(
            f"""
<tr>
  <td>
    <b>{escape(r.case_id)}</b>
    <div class="muted">{escape(r.sheet)}</div>
  </td>

  <td>
    <div>{escape(params_main)}</div>
    <details>
      <summary>展开参数（{len(params)}项）</summary>
      <div class="kv">{params_kv_html}</div>
    </details>
  </td>

  <td>{r.start_time}</td>
  <td>{r.end_time}</td>

  <td>
    <span class="status {r.status}">
      ● {r.status}
    </span>
  </td>

  <td>
    <details>
      <summary>展开备注</summary>
      {screenshots_html}
      {error_html}
    </details>
  </td>
</tr>
"""
        )

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  font-family: Arial, sans-serif;
  font-size: 13px;
  color: #222;
}}
table {{
  width: 100%;
  border-collapse: collapse;
}}
th, td {{
  border-bottom: 1px solid #ddd;
  padding: 8px;
  vertical-align: top;
}}
th {{
  background: #f5f5f5;
  cursor: pointer;
}}
.status.PASS {{ color: #1a7f37; }}
.status.FAIL {{ color: #d1242f; }}
.muted {{ color: #777; }}
details summary {{
  cursor: pointer;
  color: #0969da;
}}
.kv {{
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 4px 8px;
  margin-top: 6px;
}}
.k {{ color: #666; }}
pre {{
  background: #f6f8fa;
  padding: 8px;
  white-space: pre-wrap;
}}
</style>
</head>

<body>
<h2>Selenium 自动化测试报告</h2>
<p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

<table>
<thead>
<tr>
  <th>用例名</th>
  <th>用例参数</th>
  <th>开始时间</th>
  <th>结束时间</th>
  <th>结果</th>
  <th>备注</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>

</body>
</html>
"""

    return {
        "html": html,
        "inline_images": inline_images,
        "attachments": list(set(attachments)),
    }
