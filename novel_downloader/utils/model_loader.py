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
    REC_CHAR_MODEL_REVISION,
)


def get_rec_chinese_char_model_dir() -> Path:
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
                revision=REC_CHAR_MODEL_REVISION,
                local_dir=model_dir,
                local_dir_use_symlinks=False,
            )
        except LocalEntryNotFoundError:
            raise RuntimeError(
                f"[model] Missing model file '{fname}' and no internet connection."
            )
    return model_dir
