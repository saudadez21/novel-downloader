#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.text_utils.test_diff_display
----------------------------------------------

Unit tests for the `_char_width_space` and `diff_inline_display` functions,
which generate inline character-level diffs with visual markers and choose
space placeholders matching character width.
"""

from novel_downloader.utils.text_utils.diff_display import (
    _char_width_space,
    diff_inline_display,
)


def test_char_width_space_narrow():
    """Test that narrow (ASCII) characters map to the normal placeholder."""
    assert _char_width_space("a", normal_char="X", asian_char="Y") == "X"


def test_char_width_space_wide():
    """Test that wide (East Asian) characters map to the wide placeholder."""
    # '你' is a fullwidth character
    assert _char_width_space("你", normal_char="X", asian_char="Y") == "Y"


def test_diff_inline_display_equal():
    """Test that identical strings produce only space placeholders in the markers."""
    s = "test"
    output = diff_inline_display(s, s)
    lines = output.splitlines()

    # Check prefixes
    assert lines[0] == "-test"
    assert lines[2] == "+test"

    # Marker lines: they start with a space, then placeholders
    marker1 = lines[1][1:]
    marker2 = lines[3][1:]

    # All placeholders should be either normal space or fullwidth space
    assert all(ch in (" ", "\u3000") for ch in marker1)
    assert all(ch in (" ", "\u3000") for ch in marker2)

    # Length of markers matches length of the string
    assert len(marker1) == len(s)
    assert len(marker2) == len(s)


def test_diff_inline_display_replace():
    """Test that completely different strings produce carets for every position."""
    old = "foo"
    new = "bar"
    output = diff_inline_display(old, new)
    lines = output.splitlines()

    assert lines[0] == "-foo"
    assert lines[2] == "+bar"

    # Markers after the leading space
    marker1 = lines[1][1:]
    marker2 = lines[3][1:]

    # Since all characters differ, markers should all be '^'
    assert set(marker1) == {"^"}
    assert set(marker2) == {"^"}

    assert len(marker1) == len(old)
    assert len(marker2) == len(new)


def test_diff_inline_display_delete():
    """Test that deletions in old string are marked correctly."""
    old = "abcd"
    new = "abd"  # 'c' is deleted
    output = diff_inline_display(old, new)
    lines = output.splitlines()

    assert lines[0] == "-abcd"
    assert lines[2] == "+abd"

    marker1 = lines[1][1:]
    marker2 = lines[3][1:]

    # Should mark 'c' in marker1 with '^'
    assert marker1[2] == "^"
    assert marker2 == "   "  # No marker for deleted char


def test_diff_inline_display_insert():
    """Test that insertions in new string are marked correctly."""
    old = "abd"
    new = "abcd"  # 'c' is inserted
    output = diff_inline_display(old, new)
    lines = output.splitlines()

    assert lines[0] == "-abd"
    assert lines[2] == "+abcd"

    marker1 = lines[1][1:]
    marker2 = lines[3][1:]

    # Should mark 'c' in marker2 with '^'
    assert marker1 == "   "  # No marker for inserted char
    assert marker2[2] == "^"
