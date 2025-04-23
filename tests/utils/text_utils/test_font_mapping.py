#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.text_utils.test_font_mapping
----------------------------------------------

Unit tests for the `apply_font_mapping` function, which replaces each character
in a string based on a provided font_map, leaving unmapped characters unchanged.
"""

from novel_downloader.utils.text_utils.font_mapping import apply_font_mapping


def test_apply_font_mapping_empty_string():
    """Test that an empty string returns an empty string."""
    assert apply_font_mapping("", {}) == ""


def test_apply_font_mapping_no_mapping():
    """Test that text remains unchanged when font_map is empty."""
    text = "Hello, 世界!"
    assert apply_font_mapping(text, {}) == text


def test_apply_font_mapping_partial_mapping():
    """Test that only mapped characters are replaced."""
    text = "abcde"
    font_map = {"a": "α", "e": "ε"}
    expected = "αbcdε"
    assert apply_font_mapping(text, font_map) == expected


def test_apply_font_mapping_full_mapping():
    """Test that all characters are replaced when mapping covers every character."""
    text = "1234"
    font_map = {"1": "one", "2": "two", "3": "three", "4": "four"}
    expected = "onetwothreefour"
    assert apply_font_mapping(text, font_map) == expected


def test_apply_font_mapping_mapping_to_empty_string():
    """Test that mapping to empty string effectively removes characters."""
    text = "removeXcharactersX"
    font_map = {"X": ""}
    expected = "removecharacters"
    assert apply_font_mapping(text, font_map) == expected
