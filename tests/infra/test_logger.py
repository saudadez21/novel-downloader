import logging

import pytest
from novel_downloader.infra import logger as logger_mod


# -------------------------------
# Tests for _normalize_level
# -------------------------------
@pytest.mark.parametrize(
    "inp, expected",
    [
        (10, 10),
        ("INFO", logging.INFO),
        ("debug", logging.DEBUG),
        ("invalid", logging.INFO),
        (None, logging.INFO),
    ],
)
def test_normalize_level(inp, expected):
    assert logger_mod._normalize_level(inp) == expected


# -------------------------------
# mock TimedRotatingFileHandler
# -------------------------------
class FakeHandler:
    def __init__(self, *a, **k):
        self.level = None
        self.formatter = None

    def setLevel(self, level):
        self.level = level

    def setFormatter(self, fmt):
        self.formatter = fmt


def test_setup_logging_basic(monkeypatch, tmp_path):
    """
    Verify:
      * logger returned
      * console/file handlers created
      * directory created
      * handlers cleared on re-run (no duplicates)
      * file handler using mocked handler
    """

    # monkeypatch TimedRotatingFileHandler → FakeHandler
    monkeypatch.setattr(
        logger_mod,
        "TimedRotatingFileHandler",
        lambda *a, **k: FakeHandler(),
    )

    # monkeypatch logger_dir
    monkeypatch.setattr(logger_mod, "LOGGER_DIR", tmp_path)

    # first run
    log = logger_mod.setup_logging(log_filename="testlog", console=True, file=True)
    handlers1 = log.handlers.copy()

    assert len(handlers1) == 2  # file + console
    assert any(isinstance(h, FakeHandler) for h in handlers1)
    assert any(isinstance(h, logging.StreamHandler) for h in handlers1)

    # directory created
    assert tmp_path.exists()

    # second run should clear handlers (no duplicates)
    log2 = logger_mod.setup_logging(log_filename="testlog", console=True, file=True)
    handlers2 = log2.handlers.copy()
    assert len(handlers2) == 2

    # third-party mute loggers configured
    for name in logger_mod._MUTE_LOGGERS:
        lg = logging.getLogger(name)
        assert lg.level == logging.ERROR
        assert lg.propagate is False


def test_setup_logging_no_console(monkeypatch, tmp_path):
    """Console handler disabled."""
    monkeypatch.setattr(
        logger_mod,
        "TimedRotatingFileHandler",
        lambda *a, **k: FakeHandler(),
    )
    monkeypatch.setattr(logger_mod, "LOGGER_DIR", tmp_path)

    log = logger_mod.setup_logging(console=False, file=True)
    assert len(log.handlers) == 1
    assert isinstance(log.handlers[0], FakeHandler)


def test_setup_logging_no_file(monkeypatch, tmp_path):
    """File handler disabled."""
    monkeypatch.setattr(logger_mod, "LOGGER_DIR", tmp_path)

    log = logger_mod.setup_logging(console=True, file=False)
    assert len(log.handlers) == 1
    assert isinstance(log.handlers[0], logging.StreamHandler)
