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

import pytest

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


def test_set_and_get_cookies_with_dict(mock_state_file):
    """Test set_cookies() and get_cookies() using a dictionary."""
    sm = StateManager(path=mock_state_file)
    cookies = {"token": "abc123", "user": "alice"}
    sm.set_cookies("qidian", cookies)

    assert sm.get_cookies("qidian") == {"token": "abc123", "user": "alice"}

    # Validate file content
    data = json.loads(mock_state_file.read_text(encoding="utf-8"))
    assert data["sites"]["qidian"]["cookies"] == cookies


def test_set_cookies_with_string_parses_correctly(mock_state_file):
    """Test set_cookies() with a raw cookie string input."""
    sm = StateManager(path=mock_state_file)
    sm.set_cookies("bqg", "k1=v1; k2=v2; k3")

    expected = {"k1": "v1", "k2": "v2", "k3": ""}
    assert sm.get_cookies("bqg") == expected


def test_parse_cookie_string_edge_cases():
    """Directly test _parse_cookie_string for edge behavior."""
    sm = StateManager()  # No need for file path here
    result = sm._parse_cookie_string("a=1;  b=2;;   c  ;d=;=e")
    assert result == {"a": "1", "b": "2", "c": "", "d": "", "": "e"}


def test_set_cookies_fallback_on_non_dict_json_string(mock_state_file):
    """If JSON string is valid but not a dict, fallback to parse_cookie_string()."""
    sm = StateManager(path=mock_state_file)
    sm.set_cookies("bqg", '["a", "b"]')  # Valid JSON list
    # Fallback parser treats whole string as single item: '["a", "b"]'
    assert sm.get_cookies("bqg") == {'["a", "b"]': ""}


def test_set_cookies_invalid_type(mock_state_file):
    """Should raise TypeError if cookies is neither a dict nor a string."""
    sm = StateManager(path=mock_state_file)
    with pytest.raises(TypeError):
        sm.set_cookies("qidian", 12345)  # invalid type


def test_set_cookies_with_valid_json_string_dict(mock_state_file):
    """
    Should correctly parse and save cookies from a JSON string representing a dict.
    """
    sm = StateManager(path=mock_state_file)

    cookie_json = '{"auth": "token123", "session": "abc"}'
    sm.set_cookies("qidian", cookie_json)

    # It should parse correctly and persist
    expected = {"auth": "token123", "session": "abc"}
    assert sm.get_cookies("qidian") == expected

    # And check persisted file content
    import json

    data = json.loads(mock_state_file.read_text(encoding="utf-8"))
    assert data["sites"]["qidian"]["cookies"] == expected
