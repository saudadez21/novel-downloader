#!/usr/bin/env python3
"""
tests.config.test_loader
-------------------------

Tests for config loader functionality:
- handles valid and invalid user paths
- falls back to base.yaml if needed
- parses YAML correctly or returns empty dict on error
- logs warnings and info appropriately
"""

import pytest

from novel_downloader.config import loader


def test_load_valid_config(tmp_config_file):
    """Loading a well-formed YAML config should return the correct dict."""
    path = tmp_config_file({"general": {"request_interval": 3}})
    result = loader.load_config(path)
    assert isinstance(result, dict)
    assert result["general"]["request_interval"] == 3


def test_load_invalid_yaml(tmp_config_file):
    """YAML syntax errors should result in an empty dict."""
    path = tmp_config_file(None, filename="broken.yaml")
    path.write_text(":\n  - invalid_yaml", encoding="utf-8")

    result = loader.load_config(path)
    assert result == {}


def test_load_non_dict_yaml(tmp_config_file):
    """Top-level YAML lists should be treated as invalid and return {}."""
    path = tmp_config_file(None, filename="list.yaml")
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    result = loader.load_config(path)
    assert result == {}


# 2. load_config handling of resolve_config_path output
def test_load_missing_file_returns_empty(monkeypatch):
    """If resolve_file_path returns None, load_config should return {}."""
    monkeypatch.setattr(loader, "resolve_file_path", lambda *args, **kwargs: None)
    with pytest.raises(FileNotFoundError, match="No valid config file found"):
        loader.load_config("xxx.yaml")


def test_load_config_from_setting_file(monkeypatch, tmp_path):
    """When SETTING_FILE exists, load_config should read from it."""
    setting_file = tmp_path / "settings.yaml"
    setting_file.write_text("fallback_flag: true", encoding="utf-8")
    monkeypatch.setattr(loader, "SETTING_FILE", setting_file)
    monkeypatch.setattr(
        loader, "resolve_file_path", lambda *args, **kwargs: setting_file
    )

    res = loader.load_config(None)
    assert res.get("fallback_flag") is True
