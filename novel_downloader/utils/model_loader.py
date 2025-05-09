#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.model_loader
-----------------------------------

Utility functions for managing pre-trained model downloads.

Currently supports:
- Character recognition model for single Chinese character inference
"""

from pathlib import Path

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import LocalEntryNotFoundError

from novel_downloader.utils.constants import (
    MODEL_CACHE_DIR,
    REC_CHAR_MODEL_FILES,
    REC_CHAR_MODEL_REPO,
    REC_CHAR_VECTOR_FILES,
)


def get_rec_chinese_char_model_dir(version: str = "v1.0") -> Path:
    """
    Ensure model files are downloaded, return the directory path.
    """
    model_dir = MODEL_CACHE_DIR / "rec_chinese_char"

    model_dir.mkdir(parents=True, exist_ok=True)

    for fname in REC_CHAR_MODEL_FILES:
        try:
            hf_hub_download(
                repo_id=REC_CHAR_MODEL_REPO,
                filename=fname,
                revision=version,
                local_dir=model_dir,
                local_dir_use_symlinks=False,
            )
        except LocalEntryNotFoundError:
            raise RuntimeError(
                f"[model] Missing model file '{fname}' and no internet connection."
            )
    return model_dir


def get_rec_char_vector_dir(version: str = "v1.0") -> Path:
    """
    Ensure vector files are downloaded into a 'vector' subfolder under model directory.
    Return the directory path.
    """
    vector_dir = MODEL_CACHE_DIR / "rec_chinese_char"
    vector_dir.mkdir(parents=True, exist_ok=True)

    for fname in REC_CHAR_VECTOR_FILES:
        try:
            hf_hub_download(
                repo_id=REC_CHAR_MODEL_REPO,
                filename=fname,
                revision=version,
                local_dir=vector_dir,
                local_dir_use_symlinks=False,
            )
        except LocalEntryNotFoundError:
            raise RuntimeError(
                f"[vector] Missing vector file '{fname}' and no internet connection."
            )

    return vector_dir
