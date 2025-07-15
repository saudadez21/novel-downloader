#!/usr/bin/env python3
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

import novel_downloader.utils.file_utils.io as io_module
import pytest
from novel_downloader.utils.file_utils.io import (
    _get_non_conflicting_path,
    _write_file,
    read_binary_file,
    read_json_file,
    read_text_file,
    save_as_json,
    save_as_txt,
)


def test_get_non_conflicting_path_no_conflict(tmp_path):
    p = tmp_path / "file.txt"
    # no existing file -> same path
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


def test_write_file_type_error(tmp_path):
    """
    _write_file should raise TypeError when given non-str/bytes and dump_json=False.
    """
    p = tmp_path / "foo.bin"
    with pytest.raises(TypeError) as excinfo:
        _write_file(content=12345, filepath=p, dump_json=False)
    assert "Non-JSON content must be str or bytes." in str(excinfo.value)


def test_write_file_exception_caught(monkeypatch, tmp_path, caplog):
    """
    If writing raises any Exception (e.g. NamedTemporaryFile fails),
    _write_file logs a warning and returns False.
    """
    caplog.set_level(logging.WARNING)
    p = tmp_path / "out.txt"

    # Monkeypatch NamedTemporaryFile to raise IOError immediately
    def fake_ntf(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(io_module.tempfile, "NamedTemporaryFile", fake_ntf)

    result = _write_file(content="hello", filepath=p, dump_json=False)
    assert result is False
    # Should have logged a warning including the path and exception message
    assert any(
        record.levelno == logging.WARNING
        and "[file] Error writing" in record.getMessage()
        and "disk full" in record.getMessage()
        for record in caplog.records
    )
