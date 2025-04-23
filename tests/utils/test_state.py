#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_state
----------------------

Tests for StateManager:
- default behavior when no state file exists
- set/get language preference
- default and set/get manual_login flags
- resilience to invalid JSON
- persistence across instances
"""

import json

from novel_downloader.utils.state import StateManager


def test_get_language_default(mock_state_file):
    """
    If no state file exists, get_language() returns 'zh' without creating the file.
    """
    sm = StateManager(path=mock_state_file)
    assert sm.get_language() == "zh"
    assert not mock_state_file.exists()


def test_set_language_creates_file_and_updates(mock_state_file):
    """
    set_language() should write the file and update get_language().
    """
    sm = StateManager(path=mock_state_file)
    sm.set_language("en")
    # file must now exist
    assert mock_state_file.exists()
    data = json.loads(mock_state_file.read_text(encoding="utf-8"))
    assert data["general"]["lang"] == "en"
    # and in-memory state too
    assert sm.get_language() == "en"


def test_get_manual_login_flag_default(mock_state_file):
    """
    Unknown site defaults to manual_login=True.
    """
    sm = StateManager(path=mock_state_file)
    assert sm.get_manual_login_flag("qidian") is True


def test_set_manual_login_flag_persists(mock_state_file):
    """
    set_manual_login_flag() writes to state and get_manual_login_flag() reflects it.
    """
    sm = StateManager(path=mock_state_file)
    sm.set_manual_login_flag("qidian", False)
    # file content
    data = json.loads(mock_state_file.read_text(encoding="utf-8"))
    assert data["sites"]["qidian"]["manual_login"] is False
    # in-memory
    assert sm.get_manual_login_flag("qidian") is False
    # other site still defaults to True
    assert sm.get_manual_login_flag("bqg") is True


def test_invalid_json_is_ignored_and_overwritten(mock_state_file):
    """
    If existing file contains invalid JSON, _load() returns {}, then set_* overwrites.
    """
    # write invalid content
    mock_state_file.parent.mkdir(exist_ok=True, parents=True)
    mock_state_file.write_text("NOT JSON", encoding="utf-8")
    sm = StateManager(path=mock_state_file)
    # invalid JSON => default language
    assert sm.get_language() == "zh"
    # now set a language to overwrite
    sm.set_language("fr")
    assert sm.get_language() == "fr"
    data = json.loads(mock_state_file.read_text(encoding="utf-8"))
    assert data["general"]["lang"] == "fr"


def test_persistence_across_instances(mock_state_file):
    """State written by one instance should be visible to a new instance."""
    sm1 = StateManager(path=mock_state_file)
    sm1.set_language("es")
    # new instance reading same path
    sm2 = StateManager(path=mock_state_file)
    assert sm2.get_language() == "es"
