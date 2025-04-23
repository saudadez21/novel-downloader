#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.config.test_models
-------------------------

Test that all config dataclasses:
- Have all expected fields
- Have correct types
- Can be constructed without arguments
"""

from dataclasses import fields, is_dataclass

import pytest

from novel_downloader.config.models import (
    DownloaderConfig,
    ParserConfig,
    RequesterConfig,
    SaverConfig,
)

EXPECTED_FIELDS = {
    RequesterConfig: {
        "wait_time": int,
        "retry_times": int,
        "retry_interval": int,
        "timeout": int,
        "headless": bool,
        "user_data_folder": str,
        "profile_name": str,
        "auto_close": bool,
        "disable_images": bool,
        "mute_audio": bool,
    },
    DownloaderConfig: {
        "request_interval": int,
        "raw_data_dir": str,
        "cache_dir": str,
        "max_threads": int,
        "skip_existing": bool,
        "login_required": bool,
    },
    ParserConfig: {
        "cache_dir": str,
        "decode_font": bool,
        "use_freq": bool,
        "use_ocr": bool,
        "save_html": bool,
        "save_font_debug": bool,
    },
    SaverConfig: {
        "raw_data_dir": str,
        "output_dir": str,
        "clean_text": bool,
        "make_txt": bool,
        "make_epub": bool,
        "make_md": bool,
        "make_pdf": bool,
        "append_timestamp": bool,
        "filename_template": str,
        "include_cover": bool,
        "include_toc": bool,
    },
}


@pytest.mark.parametrize("cls", list(EXPECTED_FIELDS.keys()))
def test_dataclass_has_all_fields(cls):
    assert is_dataclass(cls), f"{cls.__name__} must be a dataclass"

    instance = cls()
    declared_fields = {f.name: f.type for f in fields(instance)}

    expected = EXPECTED_FIELDS[cls]
    assert declared_fields == expected, f"{cls.__name__} fields mismatch"

    # 类型检查（默认值是否符合注解）
    for name, expected_type in expected.items():
        value = getattr(instance, name)
        assert isinstance(value, expected_type), (
            f"{cls.__name__}.{name} default value "
            f"has type {type(value).__name__}, expected {expected_type.__name__}"
        )
