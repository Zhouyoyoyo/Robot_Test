from __future__ import annotations

import os
import smtplib
import traceback
from typing import Iterable, Dict, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.header import Header
from email.utils import formataddr
from email import encoders

from framework.utils.config_loader import load_config
from framework.utils.logger import get_logger

log = get_logger()


def send_html_mail(
    subject: str,
    html_body: str,
    *,
    inline_images: Optional[Dict[str, str]] = None,
    attachments: Optional[Iterable[str]] = None,
) -> bool:
    """
    发送 HTML 邮件（支持 CID 内嵌图片）

    参数：
        subject        : 邮件主题
        html_body     : HTML 字符串
        inline_images : cid -> image_path
        attachments   : 其他附件路径
    """
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
    alt.attach(MIMEText(html_body, "html", "utf-8"))

    # 记录 inline 图片路径，用于 attachments 去重
    inline_paths = set(inline_images.values()) if inline_images else set()


    # ===== CID 图片（作为“附件”发送，但带 Content-ID）=====
    if inline_images:
        for cid, path in inline_images.items():
            if not path or not os.path.exists(path):
                log.warning(f"[MAIL] inline image not found: cid={cid} path={path}")
                continue

            try:
                with open(path, "rb") as f:
                    img = MIMEImage(f.read())
            except Exception:
                log.warning(f"[MAIL] read inline image failed: {path}")
                continue

            # 关键：让 HTML 里可通过 cid:xxx 引用到它
            img.add_header("Content-ID", f"<{cid}>")

            # 关键：让它在邮件客户端显示为“附件”，而不是 inline 资源
            img.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(path),
            )

            msg.attach(img)

        # ===== 普通附件（跳过已作为 CID part 发送的图片）=====
        if attachments:
            for path in attachments:
                if not path:
                    continue
                if path in inline_paths:
                    # 已经作为 CID 图片 part 发过了，避免重复附件
                    continue
                if not os.path.exists(path):
                    log.warning(f"[MAIL] attachment not found: {path}")
                    continue

                part = MIMEBase("application", "octet-stream")
                try:
                    with open(path, "rb") as f:
                        part.set_payload(f.read())
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
        log.info("[MAIL] html report sent")
        return True
    except Exception:
        log.error("[MAIL] send failed")
        log.error(traceback.format_exc())
        return False
