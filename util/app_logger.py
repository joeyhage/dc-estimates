import logging
from os import environ
from logging.handlers import RotatingFileHandler


# noinspection SpellCheckingInspection
def create_logger(name, is_dev):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if is_dev:
        handler = logging.StreamHandler()
    else:
        filename = str(environ['LOG_PATH'])
        handler = RotatingFileHandler(
            filename=filename,
            maxBytes=10000000,
            backupCount=10
        )
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
