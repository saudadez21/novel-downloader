#!/usr/bin/env python3
"""
tests.config.test_models
-------------------------

Test that all config dataclasses:
- Have all expected fields
- Have correct types
- Can be constructed without arguments
"""

import types
from dataclasses import fields, is_dataclass
from typing import Literal, Union, get_args, get_origin

import pytest

from novel_downloader.config.models import (
    DownloaderConfig,
    ParserConfig,
    RequesterConfig,
    SaverConfig,
)

ModeType = Literal["browser", "session", "async"]
StorageBackend = Literal["json", "sqlite"]

EXPECTED_FIELDS = {
    RequesterConfig: {
        "retry_times": int,
        "backoff_factor": float,
        "timeout": float,
        "headless": bool,
        "user_data_folder": str,
        "profile_name": str,
        "auto_close": bool,
        "disable_images": bool,
        "mute_audio": bool,
        "mode": ModeType,
        "max_connections": int,
        "max_rps": float | None,
        "username": str,
        "password": str,
    },
    DownloaderConfig: {
        "request_interval": float,
        "raw_data_dir": str,
        "cache_dir": str,
        "parser_workers": int,
        "download_workers": int,
        "use_process_pool": bool,
        "skip_existing": bool,
        "login_required": bool,
        "save_html": bool,
        "mode": ModeType,
        "storage_backend": StorageBackend,
        "storage_batch_size": int,
    },
    ParserConfig: {
        "cache_dir": str,
        "decode_font": bool,
        "use_freq": bool,
        "use_ocr": bool,
        "use_vec": bool,
        "ocr_version": str,
        "batch_size": int,
        "gpu_mem": int,
        "gpu_id": int | None,
        "ocr_weight": float,
        "vec_weight": float,
        "save_font_debug": bool,
        "mode": ModeType,
    },
    SaverConfig: {
        "cache_dir": str,
        "raw_data_dir": str,
        "output_dir": str,
        "clean_text": bool,
        "storage_backend": StorageBackend,
        "make_txt": bool,
        "make_epub": bool,
        "make_md": bool,
        "make_pdf": bool,
        "append_timestamp": bool,
        "filename_template": str,
        "include_cover": bool,
        "include_toc": bool,
        "include_picture": bool,
    },
}


def matches_type(value: object, expected_type: type) -> bool:
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin in {Union, types.UnionType}:
        return any(matches_type(value, arg) for arg in args)

    elif origin is Literal:
        return value in args

    elif isinstance(expected_type, type):
        return isinstance(value, expected_type)

    return False


@pytest.mark.parametrize("cls", list(EXPECTED_FIELDS.keys()))
def test_dataclass_has_all_fields(cls):
    assert is_dataclass(cls), f"{cls.__name__} must be a dataclass"

    instance = cls()
    declared_fields = {f.name: f.type for f in fields(instance)}

    expected = EXPECTED_FIELDS[cls]
    assert declared_fields == expected, f"{cls.__name__} fields mismatch"

    for name, expected_type in expected.items():
        value = getattr(instance, name)
        assert matches_type(value, expected_type), (
            f"{cls.__name__}.{name} default value "
            f"has type {type(value).__name__}, expected {expected_type}"
        )
