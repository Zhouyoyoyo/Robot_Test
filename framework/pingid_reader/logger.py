"""PingID 日志模块。

PingID logger module.

作者: taobo.zhou
Author: taobo.zhou
"""

import logging


def get_logger():
    logger = logging.getLogger('PINGID')
    if not logger.handlers:
        h = logging.StreamHandler()
        f = logging.Formatter('[%(asctime)s] [PINGID] [%(levelname)s] %(message)s')
        h.setFormatter(f)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
