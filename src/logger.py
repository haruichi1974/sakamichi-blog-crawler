import datetime
import os
from logging import (
    DEBUG,
    ERROR,
    INFO,
    FileHandler,
    Formatter,
    Logger,
    StreamHandler,
    getLogger,
)

from src.args import get_option

log_dir = os.path.join(os.getcwd(), "log")


def create_logger(name) -> Logger:
    args = get_option()
    LOG_LEVEL = "DEBUG" if args.debug else "INFO"

    formatter = Formatter(
        "[%(levelname)-5s] %(asctime)s [%(name)s] - %(message)s [%(filename)s - %(funcName)s()] [%(processName)s]"
    )

    logger = getLogger(name)
    logger.setLevel(LOG_LEVEL)

    handler = StreamHandler()
    handler.setLevel(DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    info_path = get_filepath(os.path.join(log_dir, "info", name))
    info_handler = FileHandler(info_path, encoding="utf-8")
    info_handler.setLevel(INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    error_path = get_filepath(os.path.join(log_dir, "error", name))
    error_handler = FileHandler(error_path, encoding="utf-8")
    error_handler.setLevel(ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_filepath(dir):
    today = datetime.datetime.now()
    today_str = today.strftime("%Y%m%d.log")

    if not (os.path.exists(dir)):
        os.makedirs(dir)

    file_path = os.path.join(dir, today_str)

    return file_path
