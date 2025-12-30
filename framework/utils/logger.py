# ============================================
# 统一日志管理模块（唯一职责：日志）
# - 控制台 + 文件双输出
# - 统一格式
# - 支持不同日志级别
# - 不依赖 pytest，不侵入业务
#
# 本版本增强：
# - 自动为每条日志注入当前用例名（test）
#   - 在 pytest 下由 tests/conftest.py 设置
#   - 非 pytest 场景默认 "-"
# ============================================

import logging
import os
from datetime import datetime
from contextvars import ContextVar

# 当前用例名（由 pytest 注入）
_CURRENT_TEST: ContextVar[str] = ContextVar("CURRENT_TEST", default="-")


def set_current_test(name: str) -> None:
    """由 pytest 在每条用例开始时调用，用于把用例名写入日志。"""
    _CURRENT_TEST.set(name or "-")


class _InjectTestNameFilter(logging.Filter):
    """确保所有日志记录都有 record.test 字段，避免 formatter KeyError。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "test"):
            record.test = _CURRENT_TEST.get()
        return True


# 日志目录（相对项目根目录）
LOG_DIR = os.path.join(os.getcwd(), "logs")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件名（按时间）
LOG_FILE = os.path.join(
    LOG_DIR,
    f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

# 全局 logger 名称（统一）
LOGGER_NAME = "automation_logger"


def get_logger() -> logging.Logger:
    """获取全局 logger（只初始化一次）。"""
    logger = logging.getLogger(LOGGER_NAME)

    # 防止重复添加 handler（pytest 多次 import / xdist 场景）
    if getattr(logger, "_inited", False):
        return logger

    logger.setLevel(logging.DEBUG)

    # 日志格式（包含 test 字段）
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(test)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_InjectTestNameFilter())

    # 文件 Handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_InjectTestNameFilter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 避免日志重复传播到 root（pytest log_cli 等）
    logger.propagate = False

    logger._inited = True
    return logger
