#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.file_utils.test_sanitize
------------------------------------

Tests for sanitize_filename:
- Windows vs POSIX rules
- trimming dots/spaces
- reserved names handling
- max_length truncation
- fallback for empty or “dot-only” input
"""

import importlib

import pytest

# import the module under test
sanitize_mod = importlib.import_module("novel_downloader.utils.file_utils.sanitize")
sanitize_filename = sanitize_mod.sanitize_filename
_WIN_RESERVED_NAMES = sanitize_mod._WIN_RESERVED_NAMES


def _patch_os(monkeypatch, name: str):
    """Helper to replace only sanitize_mod.os with a fake having .name."""
    fake_os = type("fake_os", (), {"name": name})
    monkeypatch.setattr(sanitize_mod, "os", fake_os, raising=True)


@pytest.mark.parametrize(
    "input_name, expected",
    [
        ("simple.txt", "simple.txt"),
        ("foo/bar/baz", "foo_bar_baz"),
        ("normal_filename", "normal_filename"),
    ],
)
def test_posix_basic(monkeypatch, input_name, expected):
    _patch_os(monkeypatch, "posix")
    assert sanitize_filename(input_name) == expected


def test_posix_control_char(monkeypatch):
    _patch_os(monkeypatch, "posix")
    assert sanitize_filename("a\x00b") == "a_b"


def test_windows_illegal_chars_and_strip(monkeypatch):
    _patch_os(monkeypatch, "nt")
    raw = " a<illegal>?name*.txt "
    out = sanitize_filename(raw)
    # illegal chars removed
    for ch in '<>:"/\\|?*':
        assert ch not in out
    # spaces/dots trimmed
    assert not out.startswith(" ")
    assert not out.endswith(" ")
    assert out.endswith(".txt")


def test_reserved_windows_names(monkeypatch):
    _patch_os(monkeypatch, "nt")
    for name in ["CON", "prn", "AUX", "lpt1", "LPT9"]:
        out = sanitize_filename(name)
        assert out.lower().startswith("_" + name.lower())
        out2 = sanitize_filename(f"{name}.log")
        assert out2.startswith("_")


def test_max_length_with_extension(monkeypatch):
    _patch_os(monkeypatch, "posix")
    long_name = "x" * 300 + ".md"
    truncated = sanitize_filename(long_name, max_length=10)
    # length = 10, extension ".md" uses 3 chars (dot+2), so 7 x's
    assert truncated == "xxxxxxx.md"
    assert len(truncated) <= 10


def test_max_length_without_extension(monkeypatch):
    _patch_os(monkeypatch, "posix")
    long_name = "y" * 100
    truncated = sanitize_filename(long_name, max_length=20)
    assert truncated == "y" * 20
    assert len(truncated) == 20


def test_empty_or_dot_only(monkeypatch):
    """Empty or only-dots input must fallback to '_untitled'."""
    for platform in ("posix", "nt"):
        _patch_os(monkeypatch, platform)
        assert sanitize_filename("") == "_untitled"
        assert sanitize_filename(".") == "_untitled"
        assert sanitize_filename("...") == "_untitled"
        assert sanitize_filename("   ") == "_untitled"
