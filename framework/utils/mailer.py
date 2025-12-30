"""邮件发送模块。

Mail sender module.

Author: taobo.zhou
"""

from __future__ import annotations

import os
import smtplib
import traceback
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Iterable, Mapping

from framework.utils.config_loader import load_config
from framework.utils.logger import get_logger

log = get_logger()


def _render_summary(pytest_results: Mapping[str, Any] | None) -> str:
    if not pytest_results:
        return "<p>No pytest results provided.</p>"

    parts: list[str] = ["<ul>"]
    for key, value in pytest_results.items():
        parts.append(f"<li><strong>{key}</strong>: {value}</li>")
    parts.append("</ul>")
    return "\n".join(parts)


def _load_html_report(html_report: str | None) -> str:
    if not html_report:
        return "<p>No HTML report attached.</p>"
    if os.path.exists(html_report):
        with open(html_report, "r", encoding="utf-8") as fh:
            return fh.read()
    return html_report


def send_report(
    pytest_results: Mapping[str, Any] | None,
    html_report: str | None,
    screenshot_zip: str | None,
    *,
    subject: str = "Robot BTV 自动化测试报告",
    extra_attachments: Iterable[str] | None = None,
) -> bool:
    cfg = load_config()
    mail_cfg = cfg.get("mail", {})

    if not mail_cfg.get("enable", False):
        log.info("[MAIL] disabled")
        return False

    smtp_cfg = mail_cfg["smtp"]
    auth_cfg = mail_cfg["auth"]
    sender_cfg = mail_cfg["sender"]
    receivers = mail_cfg["receivers"]

    msg = MIMEMultipart("related")
    msg["From"] = formataddr(
        (Header(sender_cfg["name"], "utf-8").encode(), sender_cfg["address"])
    )
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = Header(subject, "utf-8")

    alt = MIMEMultipart("alternative")
    msg.attach(alt)

    html_body = _load_html_report(html_report)
    summary_block = _render_summary(pytest_results)
    full_body = f"""
    <html>
      <body>
        <h3>Pytest Summary</h3>
        {summary_block}
        <hr />
        {html_body}
      </body>
    </html>
    """
    alt.attach(MIMEText(full_body, "html", "utf-8"))

    attachments = list(extra_attachments or [])
    if screenshot_zip:
        attachments.append(screenshot_zip)

    for path in attachments:
        if not path or not os.path.exists(path):
            log.warning(f"[MAIL] attachment not found: {path}")
            continue
        part = MIMEBase("application", "octet-stream")
        try:
            with open(path, "rb") as fh:
                part.set_payload(fh.read())
        except Exception:
            log.warning(f"[MAIL] read attachment failed: {path}")
            continue

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"',
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP_SSL(
            smtp_cfg["host"],
            smtp_cfg["port"],
            timeout=30,
        )
        server.login(auth_cfg["username"], auth_cfg["password"])
        server.sendmail(sender_cfg["address"], receivers, msg.as_string())
        server.quit()
        log.info("[MAIL] report sent")
        return True
    except Exception:
        log.error("[MAIL] send failed")
        log.error(traceback.format_exc())
        return False
