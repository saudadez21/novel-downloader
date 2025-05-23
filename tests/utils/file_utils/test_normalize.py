#!/usr/bin/env python3
"""
tests.utils.test_normalize
--------------------------
"""

import logging

from novel_downloader.utils.file_utils.normalize import normalize_txt_line_endings


def test_invalid_folder(tmp_path, caplog):
    """When given a non-existent or non-dir path, logs a warning and returns."""
    nonexist = tmp_path / "nope"
    caplog.set_level(logging.WARNING)
    normalize_txt_line_endings(nonexist)
    assert "[file] Invalid folder:" in caplog.text

    # also if it's a file rather than a directory
    f = tmp_path / "somefile.txt"
    f.write_text("data")
    caplog.clear()
    normalize_txt_line_endings(f)
    assert "[file] Invalid folder:" in caplog.text


def test_normalize_single_file(tmp_path, caplog):
    """Normalize CRLF and CR to LF in a single .txt file and log successes."""
    caplog.set_level(logging.DEBUG)
    d = tmp_path / "docs"
    d.mkdir()
    txt = d / "example.txt"
    # use mixed line endings
    content = "line1\r\nline2\rline3\n"
    txt.write_text(content, encoding="utf-8", newline="")
    normalize_txt_line_endings(d)

    # file content should now only have '\n'
    new = txt.read_text(encoding="utf-8")
    assert new.splitlines() == ["line1", "line2", "line3"]

    # DEBUG log for normalization and INFO summary
    assert f"Normalized: {txt}" in caplog.text
    assert "[file] Completed. Success: 1, Failed: 0" in caplog.text


def test_normalize_recursive(tmp_path, caplog):
    """Files in nested dirs are also normalized."""
    caplog.set_level(logging.DEBUG)
    base = tmp_path / "base"
    (base / "sub").mkdir(parents=True)
    f1 = base / "a.txt"
    f2 = base / "sub" / "b.txt"
    for f in (f1, f2):
        f.write_text("x\r\ny\rz\n", encoding="utf-8", newline="")
    normalize_txt_line_endings(base)

    # both files normalized
    assert f1.read_text(encoding="utf-8").splitlines() == ["x", "y", "z"]
    assert f2.read_text(encoding="utf-8").splitlines() == ["x", "y", "z"]

    # two debug logs and summary count 2
    assert f"Normalized: {f1}" in caplog.text
    assert f"Normalized: {f2}" in caplog.text
    assert "[file] Completed. Success: 2, Failed: 0" in caplog.text


def test_normalize_with_failures(tmp_path, caplog):
    """Unreadable or undecodable files are counted as failures."""
    caplog.set_level(logging.DEBUG)
    d = tmp_path / "fld"
    d.mkdir()
    good = d / "good.txt"
    bad = d / "bad.txt"
    good.write_text("ok\r\n", encoding="utf-8", newline="")
    # write invalid UTF-8 bytes
    bad.write_bytes(b"\xff\xfe\xff")

    normalize_txt_line_endings(d)

    # good file normalized
    assert good.read_text(encoding="utf-8").splitlines() == ["ok"]
    # bad file left unchanged on disk (binary content), read as bytes
    assert bad.read_bytes() == b"\xff\xfe\xff"

    # logs: one normalized, one failed
    assert f"Normalized: {good}" in caplog.text
    assert "[file] Failed:" in caplog.text and str(bad) in caplog.text
    # summary indicates 1 success, 1 failure
    assert "[file] Completed. Success: 1, Failed: 1" in caplog.text
