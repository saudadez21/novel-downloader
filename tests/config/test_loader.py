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

import yaml

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


# 2. resolve_config_path priority order
def test_resolve_config_path_user(tmp_config_file):
    """If user provides a valid path, resolve_config_path should return it."""
    path = tmp_config_file({"foo": "bar"}, filename="conf.yaml")
    got = loader.resolve_config_path(path)
    assert got == path


def test_resolve_config_path_local(tmp_path, monkeypatch):
    """If ./settings.yaml exists in cwd, it should be chosen next."""
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    local = project / "settings.yaml"
    local.write_text("foo: bar", encoding="utf-8")

    got = loader.resolve_config_path(None)
    assert got == local


def test_resolve_config_path_setting_file(tmp_path, monkeypatch, fake_fallback_file):
    """If SETTING_FILE exists, resolve_config_path should return it."""
    setting = tmp_path / "global.yaml"
    setting.write_text("global_flag: true", encoding="utf-8")
    monkeypatch.setattr(loader, "SETTING_FILE", setting)

    got = loader.resolve_config_path(None)
    assert got == setting


def test_resolve_config_path_fallback(monkeypatch, fake_fallback_file, dummy_logger):
    """
    If no user file, local file, or setting file exists,
    resolve_config_path must fall back to BASE_CONFIG_PATH.
    """
    # Point SETTING_FILE to a non-existent file
    monkeypatch.setattr(loader, "SETTING_FILE", Path("does_not_exist.yaml"))
    got = loader.resolve_config_path(None)

    # It should return the internal BASE_CONFIG_PATH
    assert got == loader.BASE_CONFIG_PATH
    assert got.name == loader.BASE_CONFIG_PATH.name

    # Ensure we logged a debug about falling back to the internal base config
    assert any(
        lvl == "debug" and "Falling back to internal base config" in msg
        for lvl, msg in dummy_logger
    )


# 3. load_config handling of resolve_config_path output
def test_load_missing_file_returns_empty(monkeypatch):
    """If resolve_config_path returns None, load_config should return {}."""
    monkeypatch.setattr(loader, "resolve_config_path", lambda _: None)
    res = loader.load_config("xxx.yaml")
    assert res == {}


def test_load_config_from_setting_file(monkeypatch, tmp_path):
    """When SETTING_FILE exists, load_config should read from it."""
    setting_file = tmp_path / "settings.yaml"
    setting_file.write_text("fallback_flag: true", encoding="utf-8")
    monkeypatch.setattr(loader, "SETTING_FILE", setting_file)
    monkeypatch.setattr(loader, "resolve_config_path", lambda _: setting_file)

    res = loader.load_config(None)
    assert res.get("fallback_flag") is True


# 4. Optional: test caching behavior (if supported)
def test_load_config_cache(tmp_config_file, monkeypatch):
    """
    If cached_load_config caches the result, subsequent reads of the same file
    should return the original data even if the file changes.
    """
    path = tmp_config_file({"a": 1})
    first = loader.load_config(path)

    # Modify the file
    path.write_text(yaml.safe_dump({"a": 2}), encoding="utf-8")
    second = loader.load_config(path)

    # If cache is in effect, second == first
    assert second == first

    # If the decorator provides clear_cache, ensure it works
    if hasattr(loader.load_config, "clear_cache"):
        loader.load_config.clear_cache()
        third = loader.load_config(path)
        assert third["a"] == 2
