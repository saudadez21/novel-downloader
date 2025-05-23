#!/usr/bin/env python3
"""
tests.conftest
--------------------------

Provides reusable pytest fixtures for testing config and state modules:

- fake_fallback_file: simulate an internal base.yaml fallback for loader tests
- tmp_config_file:    helper to create temporary YAML config files
- dummy_logger:       capture and inspect logger output
- mock_state_file:    redirect STATE_FILE to a temp path
"""

import pytest
import yaml


# -----------------------------------------------------------------------------
# Fixture: simulate importlib.resources.files().joinpath("base.yaml")
# -----------------------------------------------------------------------------
@pytest.fixture
def fake_fallback_file(tmp_path):
    fake_base = tmp_path / "base.yaml"
    fake_base.write_text("fallback_flag: true", encoding="utf-8")

    class DummyFiles:
        def joinpath(self, name):
            # always return our fake_base regardless of name
            return fake_base

    return DummyFiles()


# -----------------------------------------------------------------------------
# Fixture: helper to write a dict to a temp YAML file and return its Path
# -----------------------------------------------------------------------------
@pytest.fixture
def tmp_config_file(tmp_path):
    """
    Return a function that creates a YAML file under tmp_path and returns its Path.
    If config_dict is given, write its contents; otherwise create an empty file.
    """

    def _make(config_dict=None, filename="settings.yaml"):
        path = tmp_path / filename
        if config_dict is not None:
            path.write_text(yaml.safe_dump(config_dict), encoding="utf-8")
        else:
            path.write_text("", encoding="utf-8")
        return path

    return _make


# -----------------------------------------------------------------------------
# Fixture: capture and inspect calls to the module logger
# -----------------------------------------------------------------------------
@pytest.fixture
def dummy_logger(monkeypatch):
    """
    Replace the config loader's logger with a dummy that records messages.
    Returns a list you can inspect in tests.
    """
    logs = []

    class DummyLogger:
        def warning(self, msg, *args, **kwargs):
            logs.append(("warning", msg % args))

        def info(self, msg, *args, **kwargs):
            logs.append(("info", msg % args))

        def error(self, msg, *args, **kwargs):
            logs.append(("error", msg % args))

        def debug(self, msg, *args, **kwargs):
            logs.append(("debug", msg % args))

    # patch the logger in the loader module
    from novel_downloader.config import loader

    monkeypatch.setattr(loader, "logger", DummyLogger())
    return logs


# -----------------------------------------------------------------------------
# Fixture: redirect STATE_FILE to a temp file for state manager tests
# -----------------------------------------------------------------------------
@pytest.fixture
def mock_state_file(tmp_path, monkeypatch):
    """
    Redirect the STATE_FILE constant in the state manager to a temp file.
    Returns the Path to that file.
    """
    fake_state = tmp_path / "state.json"
    # ensure parent exists
    fake_state.parent.mkdir(parents=True, exist_ok=True)
    # patch the constant
    from novel_downloader.utils import state as _state_mod

    monkeypatch.setattr(_state_mod, "STATE_FILE", fake_state)
    return fake_state
