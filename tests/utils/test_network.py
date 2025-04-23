#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_network
------------------------

Tests for network utilities in novel_downloader.utils.network:
- http_get_with_retry retry logic
- download_image_as_bytes: URL normalization, skip/overwrite/rename
- download_font_file: URL validation, skip, rename, and streaming download
"""

import logging
import random
import time

import requests

from novel_downloader.utils.network import (
    _DEFAULT_CHUNK_SIZE,
    download_font_file,
    download_image_as_bytes,
    http_get_with_retry,
)


class DummyResponse:
    def __init__(self, ok=True, content=b"", chunks=None):
        self.ok = ok
        self.content = content
        self._chunks = chunks or []

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError("status error")

    def iter_content(self, chunk_size=_DEFAULT_CHUNK_SIZE):
        for chunk in self._chunks:
            yield chunk


# ---------- http_get_with_retry tests ----------


def test_http_get_with_retry_success(monkeypatch):
    calls = []

    def fake_get(url, timeout, headers, stream):
        calls.append((url, timeout, headers, stream))
        return DummyResponse(ok=True, content=b"OK")

    monkeypatch.setattr(requests, "get", fake_get)
    resp = http_get_with_retry("http://example.com", retries=2, timeout=1, backoff=0)
    assert resp is not None
    assert resp.content == b"OK"
    assert calls == [("http://example.com", 1, None, False)]


def test_http_get_with_retry_retry_and_success(monkeypatch):
    attempts = {"count": 0}

    def fake_get(url, timeout, headers, stream):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise requests.RequestException("fail")
        return DummyResponse(ok=True, content=b"RETRY_OK")

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    resp = http_get_with_retry("url", retries=3, timeout=1, backoff=0.1)
    assert resp.content == b"RETRY_OK"
    assert attempts["count"] == 2


def test_http_get_with_retry_all_fail(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.RequestException()),
    )
    monkeypatch.setattr(time, "sleep", lambda s: None)
    resp = http_get_with_retry("url", retries=2, timeout=1, backoff=0)
    assert resp is None
    assert "Failed after 2 attempts" in caplog.text


# ---------- download_image_as_bytes tests ----------


def test_download_image_protocol_and_save(monkeypatch, tmp_path):
    # simulate network fetch
    monkeypatch.setattr(
        "novel_downloader.utils.network.http_get_with_retry",
        lambda url, **kw: DummyResponse(ok=True, content=b"IMG"),
    )
    data = download_image_as_bytes("//example.com/pic.png", tmp_path)
    assert data == b"IMG"
    # file should have been written
    assert (tmp_path / "pic.png").read_bytes() == b"IMG"


def test_download_image_skip_existing(monkeypatch, tmp_path):
    url = "http://test.com/x.png"
    p = tmp_path / "x.png"
    p.write_bytes(b"EXIST")
    # skip should read from disk
    out = download_image_as_bytes(url, tmp_path, on_exist="skip")
    assert out == b"EXIST"


def test_download_image_rename(monkeypatch, tmp_path):
    url = "http://site.com/a.png"
    orig = tmp_path / "a.png"
    orig.write_bytes(b"OLD")
    # simulate network fetch
    monkeypatch.setattr(
        "novel_downloader.utils.network.http_get_with_retry",
        lambda *args, **kwargs: DummyResponse(ok=True, content=b"NEW"),
    )
    out = download_image_as_bytes(url, tmp_path, on_exist="rename")
    assert out == b"NEW"
    # original unchanged, new file a_1.png created
    assert orig.read_bytes() == b"OLD"
    assert (tmp_path / "a_1.png").read_bytes() == b"NEW"


# ---------- download_font_file tests ----------


def test_download_font_file_invalid_url(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    path = download_font_file("not_a_url", tmp_path)
    assert path is None
    assert "Invalid URL" in caplog.text


def test_download_font_file_no_filename(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    path = download_font_file("https://example.com/", tmp_path)
    assert path is None
    assert "Could not extract filename" in caplog.text


def test_download_font_file_skip_existing(monkeypatch, tmp_path):
    url = "https://example.com/font.ttf"
    f = tmp_path / "font.ttf"
    f.write_bytes(b"FONT")
    out = download_font_file(url, tmp_path, on_exist="skip")
    assert out == f


def test_download_font_file_success(monkeypatch, tmp_path):
    url = "https://example.com/font.ttf"
    # simulate streaming response
    resp = DummyResponse(ok=True, chunks=[b"A", b"B", b""])
    monkeypatch.setattr(
        "novel_downloader.utils.network.http_get_with_retry",
        lambda *args, **kwargs: resp,
    )
    path = download_font_file(url, tmp_path, on_exist="overwrite")
    assert path == tmp_path / "font.ttf"
    assert path.read_bytes() == b"AB"


def test_download_font_file_rename(monkeypatch, tmp_path):
    url = "https://example.com/font.ttf"
    orig = tmp_path / "font.ttf"
    orig.write_bytes(b"OLD")
    resp = DummyResponse(ok=True, chunks=[b"X", b"Y", b""])
    monkeypatch.setattr(
        "novel_downloader.utils.network.http_get_with_retry",
        lambda *args, **kwargs: resp,
    )
    out = download_font_file(url, tmp_path, on_exist="rename")
    assert out.name.startswith("font_")
    # should not overwrite orig
    assert orig.read_bytes() == b"OLD"
    # and new file exists
    files = list(tmp_path.iterdir())
    assert any(p.name.startswith("font_") and p.read_bytes() == b"XY" for p in files)
