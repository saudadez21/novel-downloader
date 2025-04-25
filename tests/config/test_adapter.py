#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.config.test_adapter
--------------------------

Test suite for ConfigAdapter:

ensures it can correctly parse `book_ids` from different formats.
"""

import pytest

from novel_downloader.config import ConfigAdapter

# ---------- get_book_ids ----------


def test_get_book_ids_from_string():
    config = {"sites": {"qidian": {"book_ids": "1234567890"}}}
    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == ["1234567890"]


def test_get_book_ids_from_integer():
    config = {"sites": {"qidian": {"book_ids": 1234567890}}}
    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == ["1234567890"]


def test_get_book_ids_from_list():
    config = {"sites": {"qidian": {"book_ids": ["111", "222", 333]}}}
    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == ["111", "222", "333"]


def test_get_book_ids_invalid_type():
    config = {"sites": {"qidian": {"book_ids": {"not": "a list"}}}}
    adapter = ConfigAdapter(config, site="qidian")

    with pytest.raises(ValueError, match="book_ids must be a list or string"):
        adapter.get_book_ids()


def test_get_book_ids_missing_key():
    config = {
        "sites": {
            "qidian": {
                # no book_ids key
            }
        }
    }
    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == []


def test_set_site_switches_target():
    config = {
        "sites": {"qidian": {"book_ids": ["111", "222"]}, "bqg": {"book_ids": "999"}}
    }

    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == ["111", "222"]

    adapter.set_site("bqg")
    assert adapter.get_book_ids() == ["999"]


def test_set_site_to_empty():
    config = {"sites": {"qidian": {"book_ids": ["123"]}}}

    adapter = ConfigAdapter(config, site="qidian")
    assert adapter.get_book_ids() == ["123"]

    adapter.set_site("fake_site")
    assert adapter.get_book_ids() == []


# ---------- RequesterConfig ----------
def test_requester_config_defaults():
    adapter = ConfigAdapter(config={}, site="qidian")
    cfg = adapter.get_requester_config()
    assert cfg.wait_time == 5
    assert cfg.headless is True
    assert cfg.user_data_folder == "./user_data"


def test_requester_config_custom():
    config = {
        "requests": {
            "wait_time": 2,
            "retry_times": 1,
            "headless": False,
            "user_data_folder": "/custom",
        }
    }
    adapter = ConfigAdapter(config, "qidian")
    cfg = adapter.get_requester_config()
    assert cfg.wait_time == 2
    assert cfg.retry_times == 1
    assert cfg.headless is False
    assert cfg.user_data_folder == "/custom"


# ---------- DownloaderConfig ----------
def test_downloader_config_defaults():
    adapter = ConfigAdapter(config={}, site="qidian")
    cfg = adapter.get_downloader_config()
    assert cfg.request_interval == 5
    assert cfg.cache_dir == "./cache"
    assert cfg.login_required is False
    assert cfg.save_html is False


def test_downloader_config_combined():
    config = {
        "general": {
            "request_interval": 3,
            "cache_dir": "/tmp/cache",
            "debug": {"save_html": True},
        },
        "sites": {"qidian": {"login_required": True}},
    }
    adapter = ConfigAdapter(config, "qidian")
    cfg = adapter.get_downloader_config()
    assert cfg.request_interval == 3
    assert cfg.login_required is True
    assert cfg.cache_dir == "/tmp/cache"
    assert cfg.save_html is True


# ---------- ParserConfig ----------
def test_parser_config_defaults():
    adapter = ConfigAdapter(config={}, site="qidian")
    cfg = adapter.get_parser_config()
    assert cfg.decode_font is False


def test_parser_config_combined():
    config = {
        "general": {"cache_dir": "./tmp"},
        "sites": {"qidian": {"decode_font": True, "save_font_debug": True}},
    }
    adapter = ConfigAdapter(config, "qidian")
    cfg = adapter.get_parser_config()
    assert cfg.cache_dir == "./tmp"
    assert cfg.decode_font is True
    assert cfg.save_font_debug is True


# ---------- SaverConfig ----------
def test_saver_config_defaults():
    adapter = ConfigAdapter(config={}, site="qidian")
    cfg = adapter.get_saver_config()
    assert cfg.output_dir == "./downloads"
    assert cfg.make_txt is True
    assert cfg.make_epub is False
    assert cfg.filename_template == "{title}_{author}"


def test_saver_config_custom_all():
    config = {
        "general": {"raw_data_dir": "raw/", "output_dir": "out/"},
        "output": {
            "clean_text": False,
            "formats": {"make_txt": False, "make_pdf": True},
            "naming": {"append_timestamp": False, "filename_template": "{title}"},
            "epub": {"include_cover": False, "include_toc": True},
        },
    }
    adapter = ConfigAdapter(config, "qidian")
    cfg = adapter.get_saver_config()
    assert cfg.raw_data_dir == "raw/"
    assert cfg.output_dir == "out/"
    assert cfg.make_txt is False
    assert cfg.make_pdf is True
    assert cfg.append_timestamp is False
    assert cfg.include_toc is True
