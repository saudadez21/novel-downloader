#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_model_loader
-----------------------------
"""

from pathlib import Path

import pytest
from huggingface_hub.utils import LocalEntryNotFoundError

import novel_downloader.utils.model_loader as model_loader
from novel_downloader.utils.constants import (
    REC_CHAR_MODEL_FILES,
    REC_CHAR_MODEL_REPO,
    REC_CHAR_VECTOR_FILES,
)
from novel_downloader.utils.model_loader import (
    get_rec_char_vector_dir,
    get_rec_chinese_char_model_dir,
)


def test_get_rec_chinese_char_model_dir_success(monkeypatch, tmp_path):
    """Ensure get_rec_chinese_char_model_dir downloads all model files."""
    # Capture calls and simulate file creation
    calls = []

    def fake_hf_download(
        repo_id, filename, revision, local_dir, local_dir_use_symlinks
    ):
        calls.append((repo_id, filename, revision, Path(local_dir)))
        # simulate writing the file
        (Path(local_dir) / filename).write_text("dummy")

    # Redirect cache dir to tmp_path
    monkeypatch.setattr(model_loader, "MODEL_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(model_loader, "hf_hub_download", fake_hf_download)

    out_dir = get_rec_chinese_char_model_dir(version="v1.2")
    expected_dir = tmp_path / "cache" / "rec_chinese_char"
    assert out_dir == expected_dir
    # Directory should exist
    assert expected_dir.exists() and expected_dir.is_dir()
    # hf_hub_download called once per expected file
    assert len(calls) == len(REC_CHAR_MODEL_FILES)
    for idx, fname in enumerate(REC_CHAR_MODEL_FILES):
        repo_id, filename, revision, local_dir = calls[idx]
        assert repo_id == REC_CHAR_MODEL_REPO
        assert filename == fname
        assert revision == "v1.2"
        assert local_dir == expected_dir
        # file created
        assert (expected_dir / fname).read_text() == "dummy"


def test_get_rec_chinese_char_model_dir_missing(monkeypatch, tmp_path):
    """If a model file is missing, RuntimeError is raised."""

    def fake_hf_download(
        repo_id, filename, revision, local_dir, local_dir_use_symlinks
    ):
        raise LocalEntryNotFoundError("not found")

    monkeypatch.setattr(model_loader, "MODEL_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(model_loader, "hf_hub_download", fake_hf_download)

    first_fname = REC_CHAR_MODEL_FILES[0]
    with pytest.raises(RuntimeError) as excinfo:
        get_rec_chinese_char_model_dir()
    msg = str(excinfo.value)
    assert "[model] Missing model file" in msg
    assert first_fname in msg


def test_get_rec_char_vector_dir_success(monkeypatch, tmp_path):
    """Ensure get_rec_char_vector_dir downloads all vector files."""
    calls = []

    def fake_hf_download(
        repo_id, filename, revision, local_dir, local_dir_use_symlinks
    ):
        calls.append((repo_id, filename, revision, Path(local_dir)))
        (Path(local_dir) / filename).write_text("vec")

    monkeypatch.setattr(model_loader, "MODEL_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(model_loader, "hf_hub_download", fake_hf_download)

    out_dir = get_rec_char_vector_dir(version="v3.4")
    expected_dir = tmp_path / "cache" / "rec_chinese_char"
    assert out_dir == expected_dir
    assert expected_dir.exists()
    assert len(calls) == len(REC_CHAR_VECTOR_FILES)
    for idx, fname in enumerate(REC_CHAR_VECTOR_FILES):
        repo_id, filename, revision, local_dir = calls[idx]
        assert repo_id == REC_CHAR_MODEL_REPO
        assert filename == fname
        assert revision == "v3.4"
        assert local_dir == expected_dir
        assert (expected_dir / fname).read_text() == "vec"


def test_get_rec_char_vector_dir_missing(monkeypatch, tmp_path):
    """If a vector file is missing, RuntimeError is raised."""

    def fake_hf_download(
        repo_id, filename, revision, local_dir, local_dir_use_symlinks
    ):
        raise LocalEntryNotFoundError("no vec")

    monkeypatch.setattr(model_loader, "MODEL_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(model_loader, "hf_hub_download", fake_hf_download)

    first_vec = REC_CHAR_VECTOR_FILES[0]
    with pytest.raises(RuntimeError) as excinfo:
        get_rec_char_vector_dir()
    msg = str(excinfo.value)
    assert "[vector] Missing vector file" in msg
    assert first_vec in msg
