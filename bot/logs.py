import logging
import pathlib
import sys
from logging import handlers

from colorlog import ColoredFormatter
from pythonjsonlogger.json import JsonFormatter

from .config import settings


def get_logs_directory() -> pathlib.Path:
    """
    Returns the directory path for log files.

    This function constructs the directory path for the log files
    using the current working directory and the directory name
    specified in the logger settings.

    The directory might not exist. Make sure to call create_logs_directory before normalizing or using the path.

    Returns:
        pathlib.Path: The path to the logs directory.
    """
    return pathlib.Path.cwd().joinpath(settings.logger_settings.directory)


def get_file_path() -> pathlib.Path:
    """
    Returns the full file path for the log file.

    This function constructs the full file path for the log file using the
    logs directory and the file name specified in the logger settings.

    Raises:
        FileNotFoundError: If the logs directory does not exist. (create_logs_directory should be called first)

    Returns:
        pathlib.Path: The complete path to the log file.
    """
    return (
        pathlib.Path(get_logs_directory())
        .resolve(True)
        .joinpath(settings.logger_settings.file_name)
    )


def create_logs_directory() -> None:
    """
    Creates the logs directory and parents if not already created.

    This is idempotent, so it is safe to call multiple times.
    """
    get_logs_directory().mkdir(parents=True, exist_ok=True)


json_formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
color_formatter = ColoredFormatter(
    "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s [%(name)s] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    style="%",
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(color_formatter)

if not get_logs_directory().exists():
    create_logs_directory()

file_handler = handlers.RotatingFileHandler(
    filename=str(get_file_path()),
    encoding="utf-8",
    maxBytes=10 * 1024 * 1024,  # 10 MiB
    backupCount=5,
)
file_handler.setFormatter(json_formatter)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance with the specified name and log level.

    This function creates and returns a logger with handlers for both console
    and file output. If the handlers are already present, it simply returns
    the existing logger.

    It uses a rotating file handler to manage log file size and retention.

    Args:
        name (str): The name of the logger.
        level (logging._Level, optional): The logging level to set. Defaults to logging.INFO.

    Returns:
        logging.Logger: The configured logger instance.
    """

    logger = logging.getLogger(name)
    if console_handler in logger.handlers and file_handler in logger.handlers:
        return logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(level)
    return logger
