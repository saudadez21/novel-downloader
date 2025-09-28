#!/usr/bin/env python3
"""
novel_downloader.infra.logger
-----------------------------

Provides a configurable logging setup for Python applications.
"""

from __future__ import annotations

__all__ = ["setup_logging"]

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from novel_downloader.infra.paths import LOGGER_DIR, PACKAGE_NAME

_MUTE_LOGGERS: set[str] = {
    "fontTools.ttLib.tables._p_o_s_t",
}


def _normalize_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return logging._nameToLevel.get(level.upper(), logging.INFO)
    return logging.INFO


def setup_logging(
    log_filename: str | None = None,
    console_level: int | str = "INFO",
    file_level: int | str = "DEBUG",
    log_dir: str | Path | None = None,
    *,
    console: bool = True,
    file: bool = True,
    backup_count: int = 7,
    when: str = "midnight",
) -> logging.Logger:
    """
    Create and configure a package logger with optional console and file handlers.

    :param log_filename: Base log file name (without date suffix).
    :param console_level: Minimum level for the console handler (string or int).
    :param file_level: Minimum level for the file handler (string or int).
    :param log_dir: Directory where log files will be saved.
    :param console: Add a console handler.
    :param file: Add a file handler.
    :param backup_count: How many rotated files to keep.
    :param when: Rotation interval for TimedRotatingFileHandler (e.g., "midnight").
    :return: The configured logger.
    """
    # Tame noisy third-party loggers
    for name in _MUTE_LOGGERS:
        ml = logging.getLogger(name)
        ml.setLevel(logging.ERROR)
        ml.propagate = False

    logger = logging.getLogger(PACKAGE_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # otherwise may affected by PaddleOCR

    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler (rotates daily)
    if file:
        file_level = _normalize_level(file_level)

        base_dir = Path(log_dir) if log_dir else LOGGER_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        base_name = log_filename or PACKAGE_NAME
        log_path = base_dir / f"{base_name}.log"

        fh = TimedRotatingFileHandler(
            filename=log_path,
            when=when,
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
            utc=False,
            delay=True,
        )

        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(file_formatter)
        fh.setLevel(file_level)
        logger.addHandler(fh)

        print(f"Logging to {log_path}")

    # Console handler
    if console:
        console_level = _normalize_level(console_level)

        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)

    return logger
