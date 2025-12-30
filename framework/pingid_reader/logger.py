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
