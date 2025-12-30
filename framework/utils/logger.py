"""日志管理模块。

Logger module.

作者: taobo.zhou
Author: taobo.zhou
"""

import logging
import os
from datetime import datetime
from contextvars import ContextVar

_CURRENT_TEST: ContextVar[str] = ContextVar("CURRENT_TEST", default="-")


def set_current_test(name: str) -> None:
    _CURRENT_TEST.set(name or "-")


class _InjectTestNameFilter(logging.Filter):
    """日志过滤器。

    Logger filter.

    作者: taobo.zhou
    Author: taobo.zhou
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "test"):
            record.test = _CURRENT_TEST.get()
        return True


LOG_DIR = os.path.join(os.getcwd(), "logs")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

LOGGER_NAME = "automation_logger"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    if getattr(logger, "_inited", False):
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(test)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_InjectTestNameFilter())

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_InjectTestNameFilter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    logger._inited = True
    return logger


def get_page_logger(page_name: str | None = None) -> logging.Logger:
    logger = get_logger()
    if page_name:
        logger = logging.LoggerAdapter(logger, {"page": page_name})
    return logger
