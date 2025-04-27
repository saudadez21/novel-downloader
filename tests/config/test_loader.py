#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.config.test_loader
-------------------------

Tests for config loader functionality:
- handles valid and invalid user paths
- falls back to base.yaml if needed
- parses YAML correctly or returns empty dict on error
- logs warnings and info appropriately
"""

from pathlib import Path

from novel_downloader.config import loader
from novel_downloader.config.loader import load_config, resolve_config_path


def test_load_valid_config(tmp_config_file):
    """Test loading a well-formed YAML config file."""
    path = tmp_config_file({"general": {"request_interval": 3}})
    result = load_config(path)
    assert isinstance(result, dict)
    assert result["general"]["request_interval"] == 3


def test_load_invalid_yaml(tmp_config_file):
    """YAML syntax error should fallback to empty dict."""
    # Write broken YAML
    path = tmp_config_file(None, filename="broken.yaml")
    path.write_text(":\n  - invalid_yaml", encoding="utf-8")

    result = load_config(path)
    assert result == {}


def test_load_non_dict_yaml(tmp_config_file):
    """Top-level YAML list should be treated as invalid and return {}."""
    path = tmp_config_file(None, filename="list.yaml")
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    result = load_config(path)
    assert result == {}


def test_load_missing_file_returns_fallback(fake_fallback_file, monkeypatch):
    """Missing user config should fallback to internal base.yaml contents."""
    monkeypatch.setattr(loader, "files", lambda _: fake_fallback_file)
    fake_path = Path("fake_path.yaml")
    monkeypatch.setattr(loader, "SETTING_FILE", fake_path)
    result = load_config("nonexistent.yaml")
    assert result.get("fallback_flag") is True


def test_resolve_config_path_valid(tmp_config_file):
    """resolve_config_path returns a valid Path when file exists."""
    path = tmp_config_file({"foo": "bar"}, filename="conf.yaml")
    result = resolve_config_path(path)
    assert isinstance(result, Path)
    assert result == path


def test_resolve_config_path_fallback(fake_fallback_file, monkeypatch):
    """resolve_config_path falls back to internal base.yaml path."""
    monkeypatch.setattr(loader, "files", lambda _: fake_fallback_file)
    fake_path = Path("fake_path.yaml")
    monkeypatch.setattr(loader, "SETTING_FILE", fake_path)
    path = resolve_config_path(None)
    assert path.name == "base.yaml" or path.name == "base.yaml"
    text = path.read_text(encoding="utf-8").strip()
    assert "fallback_flag: true" in text


def test_resolve_config_path_logs(monkeypatch, fake_fallback_file, dummy_logger):
    """resolve_config_path logs warning on missing user file, then info on fallback."""
    # point loader.files to our fake fallback
    monkeypatch.setattr(loader, "files", lambda _: fake_fallback_file)
    fake_path = Path("fake_path.yaml")
    monkeypatch.setattr(loader, "SETTING_FILE", fake_path)
    bad_path = Path("does_not_exist.yaml")
    resolve_config_path(bad_path)
    # check that a warning was logged for missing file
    assert any(
        "Specified config file not found" in msg
        for level, msg in dummy_logger
        if level == "warning"
    )
    # check that fallback info was logged
    assert any(
        "internal base.yaml fallback" in msg
        for level, msg in dummy_logger
        if level == "debug"
    )


def test_resolve_config_path_to_setting_file(monkeypatch, tmp_path):
    """resolve_config_path returns SETTING_FILE if it exists."""
    setting_file = tmp_path / "settings.yaml"
    setting_file.write_text("fallback_flag: true", encoding="utf-8")

    monkeypatch.setattr(loader, "SETTING_FILE", setting_file)

    path = resolve_config_path(None)

    assert path == setting_file
    text = path.read_text(encoding="utf-8").strip()
    assert "fallback_flag: true" in text


def test_load_config_from_setting_file(monkeypatch, tmp_path):
    """load_config uses SETTING_FILE if it exists."""
    setting_file = tmp_path / "settings.yaml"
    setting_file.write_text("fallback_flag: true", encoding="utf-8")

    monkeypatch.setattr(loader, "SETTING_FILE", setting_file)

    result = load_config(None)

    assert result.get("fallback_flag") is True
