#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.file_utils.test_io
------------------------------

Tests for file I/O utilities in novel_downloader.utils.file_utils.io:
- _get_non_conflicting_path
- save_as_txt and save_as_json with overwrite/skip/rename behaviors
- read_text_file, read_json_file, read_binary_file error handling
"""

import json
import logging
import re

import pytest

import novel_downloader.utils.file_utils.io as io_module
from novel_downloader.utils.file_utils.io import (
    _get_non_conflicting_path,
    read_binary_file,
    read_json_file,
    read_text_file,
    save_as_json,
    save_as_txt,
)


def test_get_non_conflicting_path_no_conflict(tmp_path):
    p = tmp_path / "file.txt"
    # no existing file → same path
    assert _get_non_conflicting_path(p) == p


def test_get_non_conflicting_path_with_conflicts(tmp_path):
    p = tmp_path / "file.txt"
    # create several versions
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "file_1.txt").write_text("x")
    # first conflict yields file_2.txt
    out = _get_non_conflicting_path(p)
    assert out.name == "file_2.txt"
    assert not out.exists()


def test_save_as_txt_behaviors(tmp_path):
    p = tmp_path / "test.txt"

    # 1. create new
    assert save_as_txt("hello", p) is True
    assert p.read_text(encoding="utf-8") == "hello"

    # 2. skip existing
    assert save_as_txt("new", p, on_exist="skip") is False
    assert p.read_text(encoding="utf-8") == "hello"

    # 3. overwrite existing
    assert save_as_txt("world", p, on_exist="overwrite") is True
    assert p.read_text(encoding="utf-8") == "world"

    # 4. rename existing
    p.write_text("orig")
    result = save_as_txt("dup", p, on_exist="rename")
    assert result is True
    # original remains
    assert p.read_text(encoding="utf-8") == "orig"
    # renamed file exists
    renamed = tmp_path / "test_1.txt"
    assert renamed.exists()
    assert renamed.read_text(encoding="utf-8") == "dup"


def test_save_as_json_behaviors(tmp_path):
    p = tmp_path / "data.json"

    # 1. create new
    data = {"a": 1}
    assert save_as_json(data, p) is True
    assert json.loads(p.read_text(encoding="utf-8")) == data

    # 2. skip existing
    assert save_as_json({"b": 2}, p, on_exist="skip") is False
    assert json.loads(p.read_text(encoding="utf-8")) == data

    # 3. overwrite existing
    assert save_as_json({"b": 2}, p, on_exist="overwrite") is True
    assert json.loads(p.read_text(encoding="utf-8")) == {"b": 2}


def test_large_json_forces_compact_format(tmp_path, monkeypatch):
    # Patch threshold to trigger compact mode even for small input
    monkeypatch.setattr(io_module, "_JSON_INDENT_THRESHOLD", 10)

    # Simulate a large-enough JSON string
    large_data = {"key": "A" * 100}
    file_path = tmp_path / "compact.json"

    success = save_as_json(large_data, file_path)
    assert success is True

    raw = file_path.read_text(encoding="utf-8")

    # Optional: could also check len(line) == 1
    assert re.search(r"\{\s*\n", raw) is None, "Should use compact JSON format"

    # Confirm it's valid JSON and equals original
    assert json.loads(raw) == large_data


@pytest.mark.parametrize(
    "reader, content, expected",
    [
        (read_text_file, "text content", "text content"),
        (read_json_file, {"k": 5}, {"k": 5}),
        (read_binary_file, b"\x00\x01", b"\x00\x01"),
    ],
)
def test_readers_success(tmp_path, reader, content, expected):
    """Test reading valid files of each type."""
    path = tmp_path / "f"
    # write appropriate type
    if reader is read_binary_file:
        path = path.with_suffix(".bin")
        path.write_bytes(content)
    elif reader is read_json_file:
        path = path.with_suffix(".json")
        path.write_text(json.dumps(content), encoding="utf-8")
    else:
        path = path.with_suffix(".txt")
        path.write_text(content, encoding="utf-8")

    result = reader(path)
    assert result == expected


@pytest.mark.parametrize("reader", [read_text_file, read_json_file, read_binary_file])
def test_readers_failure(tmp_path, caplog, reader):
    """Test that readers return None and log a warning on missing or invalid files."""
    caplog.set_level(logging.WARNING)
    missing = tmp_path / "noexist"
    # for JSON reader, create invalid JSON
    if reader is read_json_file:
        f = missing.with_suffix(".json")
        f.write_text("{bad: json}", encoding="utf-8")
        result = reader(f)
    else:
        result = reader(missing)
    assert result is None
    # must log a warning
    assert any("Failed to read" in rec.message for rec in caplog.records)


def test_load_text_resource_success(tmp_path, monkeypatch):
    """Test that load_text_resource returns correct content for an existing file."""
    file_path = tmp_path / "sample.txt"
    expected_content = "Hello, 世界"
    file_path.write_text(expected_content, encoding="utf-8")

    monkeypatch.setattr(io_module, "files", lambda pkg: tmp_path)

    result = io_module.load_text_resource("sample.txt", package="any_pkg")
    assert result == expected_content


def test_load_text_resource_file_not_found(tmp_path, monkeypatch):
    """Test that load_text_resource raises FileNotFoundError for a missing file."""
    monkeypatch.setattr(io_module, "files", lambda pkg: tmp_path)

    with pytest.raises(FileNotFoundError):
        io_module.load_text_resource("missing.txt", package="some_pkg")


def test_load_blacklisted_words(monkeypatch):
    """
    Test that load_blacklisted_words returns a deduplicated, non-empty set of lines
    """
    dummy_text = "\n求票\n月票\n\n投票\n"

    monkeypatch.setattr(
        io_module, "load_text_resource", lambda filename, package=None: dummy_text
    )

    result = io_module.load_blacklisted_words()
    assert result == {"求票", "月票", "投票"}
