import logging
import os
import sys

import colorlog
from pythonjsonlogger.json import JsonFormatter

cout_handler = colorlog.StreamHandler(sys.stdout)
cout_handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s"
    )
)

file_handler = logging.FileHandler("latest.log")
file_handler.setFormatter(
    JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)


def setup_logger(name: str, debug: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(cout_handler)
    logger.setLevel(
        logging.DEBUG
        if debug or os.environ.get("LOGGER_DEBUG", "false").lower() == "true"
        else logging.INFO
    )
    return logger


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if file_handler not in logger.handlers:
        logger.addHandler(file_handler)
    if cout_handler not in logger.handlers:
        logger.addHandler(cout_handler)
    if os.environ.get("LOGGER_DEBUG", "false").lower() == "true":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


logs = [
    "bootstrap",
    "presence",
    "commands",
    "admin",
    "reactions",
    "plugins",
    "voice",
    "utils",
    "functions",
    "fun",
    "welcome",
]


def Logs() -> dict[str, logging.Logger]:
    r = {}
    for i in logs:
        r[i] = get_logger(i)
    return r


Log = Logs()
