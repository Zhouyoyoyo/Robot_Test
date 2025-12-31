import logging


def get_logger():
    """Author: taobo.zhou
    中文：获取 PingID 日志记录器。
    参数: 无。
    """

    logger = logging.getLogger("PINGID")
    if not logger.handlers:
        h = logging.StreamHandler()
        f = logging.Formatter("[%(asctime)s] [PINGID] [%(levelname)s] %(message)s")
        h.setFormatter(f)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
