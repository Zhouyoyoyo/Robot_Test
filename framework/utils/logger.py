import logging
import os
from datetime import datetime
from contextvars import ContextVar

_CURRENT_TEST: ContextVar[str] = ContextVar("CURRENT_TEST", default="-")


def set_current_test(name: str) -> None:
    """Author: taobo.zhou
    设置当前测试名称上下文。
    
        name: 当前测试名称。
    """

    _CURRENT_TEST.set(name or "-")


class _InjectTestNameFilter(logging.Filter):
    """Author: taobo.zhou
    日志过滤器，注入测试名称到记录中。
    Logger filter injecting test name into log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Author: taobo.zhou
        在日志记录中填充测试名称。
        
            record: 日志记录对象。
        """

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
    """Author: taobo.zhou
    获取全局日志记录器。
     无。
    """

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
    """Author: taobo.zhou
    获取页面级日志记录器。
    
        page_name: 页面名称，可为空。
    """

    logger = get_logger()
    if page_name:
        logger = logging.LoggerAdapter(logger, {"page": page_name})
    return logger
