#!/usr/bin/env python3
"""
novel_downloader.utils.logger
-----------------------------

Provides a configurable logging setup for Python applications.
Log files are rotated daily and named with the given logger name and current date.
"""

__all__ = ["setup_logging"]

import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from .constants import LOGGER_DIR, LOGGER_NAME

LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def setup_logging(
    log_filename_prefix: str | None = None,
    log_level: str | None = None,
    log_dir: str | Path | None = None,
) -> logging.Logger:
    """
    Create and configure a logger for both console and rotating file output.

    :param log_filename_prefix: Prefix for the log file name.
    :param log_level: Minimum log level to show in console
                        ("DEBUG", "INFO", "WARNING", "ERROR")
    :param log_dir: Directory where log files will be saved.
    :return: A fully configured logger instance.
    """
    ft_logger = logging.getLogger("fontTools.ttLib.tables._p_o_s_t")
    ft_logger.setLevel(logging.ERROR)
    ft_logger.propagate = False

    # Determine console level (default INFO)
    level_str: str = log_level or "INFO"
    console_level: int = LOG_LEVELS.get(level_str) or logging.INFO

    # Resolve log file path
    log_path = Path(log_dir) if log_dir else LOGGER_DIR
    log_path.mkdir(parents=True, exist_ok=True)

    # Resolve log file name
    if not log_filename_prefix:
        log_filename_prefix = LOGGER_NAME
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = log_path / f"{log_filename_prefix}_{date_str}.log"

    # Create or retrieve logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # Capture everything, filter by handlers
    logger.propagate = False

    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler: rotates at midnight, keeps 7 days of logs
    file_handler = TimedRotatingFileHandler(
        filename=str(log_filename),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=False,
    )
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    print(f"Logging to {log_path}")

    return logger
