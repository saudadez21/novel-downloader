#!/usr/bin/env python3
"""
tests.utils.test_logger
-----------------------
"""

import logging
from datetime import datetime
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytest

import novel_downloader.utils.logger as logmod
from novel_downloader.utils.logger import setup_logging


def test_setup_logging_default(monkeypatch, tmp_path, capsys):
    """
    Default setup_logging creates LOGGER_DIR, uses LOGGER_NAME, INFO console level.
    """
    monkeypatch.setattr(logmod, "LOGGER_DIR", tmp_path / "logs")
    monkeypatch.setattr(logmod, "LOGGER_NAME", "myapp")
    root = logging.getLogger()
    root.handlers.clear()

    logger = setup_logging()
    captured = capsys.readouterr()
    assert f"Logging to {tmp_path/'logs'}" in captured.out

    handlers = logger.handlers
    assert len(handlers) == 2

    # pick out the file handler by its exact class
    fh = next(h for h in handlers if isinstance(h, TimedRotatingFileHandler))
    assert fh.level == logging.DEBUG
    today = datetime.now().strftime("%Y-%m-%d")
    expected = tmp_path / "logs" / f"myapp_{today}.log"
    assert Path(fh.baseFilename) == expected

    # console handler must be the *other* handler
    ch = next(h for h in handlers if h is not fh)
    # ensure it really is the plain StreamHandler
    from logging import StreamHandler

    assert type(ch) is StreamHandler
    assert ch.level == logging.INFO


def test_setup_logging_custom_prefix_and_level_and_dir(monkeypatch, tmp_path, capsys):
    """Custom prefix, level and log_dir are honored."""
    custom_dir = tmp_path / "custom"
    # no need to monkeypatch LOGGER_DIR here
    root = logging.getLogger()
    root.handlers.clear()

    logger = setup_logging(
        log_filename_prefix="pref",
        log_level="DEBUG",
        log_dir=custom_dir,
    )
    captured = capsys.readouterr()
    assert f"Logging to {custom_dir}" in captured.out

    handlers = logger.handlers
    # file handler
    fh = next(h for h in handlers if isinstance(h, TimedRotatingFileHandler))
    today = datetime.now().strftime("%Y-%m-%d")
    assert Path(fh.baseFilename) == custom_dir / f"pref_{today}.log"
    assert fh.level == logging.DEBUG

    # console handler at DEBUG
    ch = next(h for h in handlers if isinstance(h, StreamHandler))
    assert ch.level == logging.DEBUG


def test_setup_logging_invalid_level_raises():
    """Providing an invalid log_level should raise ValueError."""
    with pytest.raises(ValueError) as excinfo:
        setup_logging(log_level="VERBOSE")
    assert "Invalid log level: VERBOSE" in str(excinfo.value)


def test_setup_logging_clears_existing_handlers(monkeypatch, tmp_path):
    """Existing handlers on root logger are cleared before adding new ones."""
    # Add a dummy handler
    root = logging.getLogger()
    dummy = StreamHandler()
    root.addHandler(dummy)
    assert root.handlers  # we have at least one

    # Redirect directory
    monkeypatch.setattr(logmod, "LOGGER_DIR", tmp_path / "logs2")
    monkeypatch.setattr(logmod, "LOGGER_NAME", "app2")
    # Call setup
    logger = setup_logging()
    # After setup, only two handlers remain
    assert len(logger.handlers) == 2
    # And dummy is not among them
    assert not any(isinstance(h, type(dummy)) and h is dummy for h in logger.handlers)


def test_fonttools_logger_configured(monkeypatch, tmp_path):
    """The fontTools logger should be set to ERROR and propagation disabled."""
    # Redirect directory so setup runs smoothly
    monkeypatch.setattr(logmod, "LOGGER_DIR", tmp_path / "logs3")
    monkeypatch.setattr(logmod, "LOGGER_NAME", "app3")
    # Ensure no side effect
    logging.getLogger().handlers.clear()

    # Before calling, ensure default might be different
    ft = logging.getLogger("fontTools.ttLib.tables._p_o_s_t")
    ft.setLevel(logging.NOTSET)
    ft.propagate = True

    setup_logging()
    # After setup_logging, it must be ERROR and propagate=False
    assert ft.level == logging.ERROR
    assert ft.propagate is False
