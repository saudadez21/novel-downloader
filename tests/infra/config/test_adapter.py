import os
import warnings
from pathlib import Path

import pytest
from novel_downloader.infra.config.adapter import ConfigAdapter
from novel_downloader.schemas import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    OCRConfig,
    ParserConfig,
    ProcessorConfig,
)


def make_adapter(cfg):
    return ConfigAdapter(cfg)


def test_get_fetcher_config_priorities():
    cfg = {
        "general": {"timeout": 99},
        "sites": {"siteA": {"timeout": 7, "max_connections": 20}},
    }
    adapter = make_adapter(cfg)
    fc = adapter.get_fetcher_config("siteA")

    assert isinstance(fc, FetcherConfig)
    # site overrides general
    assert fc.timeout == 7
    # general fallback
    assert fc.backoff_factor == 2.0
    # default fallback
    assert fc.request_interval == 0.5


def test_get_parser_config_fontocr_override():
    cfg = {
        "general": {
            "font_ocr": {"enable_ocr": True, "batch_size": 64},
        },
        "sites": {"s1": {"font_ocr": {"batch_size": 128}}},
    }
    adapter = make_adapter(cfg)
    pc = adapter.get_parser_config("s1")

    assert isinstance(pc, ParserConfig)
    assert pc.enable_ocr is True
    assert pc.batch_size == 128  # site overrides general


def test_get_parser_config_input_shape_to_tuple():
    cfg = {"general": {"font_ocr": {"input_shape": [1, 32, 32]}}}
    adapter = make_adapter(cfg)
    pc = adapter.get_parser_config("unknown")

    assert pc.ocr_cfg.input_shape == (1, 32, 32)


def test_get_client_config_basic():
    cfg = {
        "general": {
            "debug": {"save_html": True},
            "raw_data_dir": "raw",
            "output_dir": "out",
            "cache_dir": "cache",
        },
        "sites": {"a": {"workers": 10}},
    }
    adapter = make_adapter(cfg)
    cc = adapter.get_client_config("a")

    assert isinstance(cc, ClientConfig)
    assert cc.workers == 10
    assert cc.save_html is True


def test_get_exporter_config():
    cfg = {
        "sites": {"s1": {"split_mode": "chapter"}},
        "output": {
            "append_timestamp": False,
            "filename_template": "{id}",
            "include_picture": False,
        },
    }
    adapter = make_adapter(cfg)
    ec = adapter.get_exporter_config("s1")

    assert isinstance(ec, ExporterConfig)
    assert ec.append_timestamp is False
    assert ec.split_mode == "chapter"


def test_get_login_config_strip():
    cfg = {
        "sites": {"x": {"username": "  user  ", "password": " pass ", "cookies": "  "}}
    }
    adapter = make_adapter(cfg)
    out = adapter.get_login_config("x")

    assert out == {"username": "user", "password": "pass"}


def test_get_login_required_fallback():
    cfg = {"general": {"login_required": True}, "sites": {"s1": {}}}
    adapter = make_adapter(cfg)
    assert adapter.get_login_required("s1") is True

    cfg = {
        "general": {"login_required": False},
        "sites": {"s1": {"login_required": True}},
    }
    adapter = make_adapter(cfg)
    assert adapter.get_login_required("s1") is True


def test_get_export_fmt_list():
    cfg = {"sites": {"s": {"formats": ["txt", "epub"]}}}
    adapter = make_adapter(cfg)
    assert adapter.get_export_fmt("s") == ["txt", "epub"]


def test_get_export_fmt_dict_warns():
    cfg = {"output": {"formats": {"make_txt": True, "make_epub": False}}}
    adapter = make_adapter(cfg)

    with warnings.catch_warnings(record=True) as w:
        result = adapter.get_export_fmt("unknown")

    assert any("legacy" in str(wi.message) for wi in w)
    assert result == ["txt"]


def test_get_export_fmt_empty():
    adapter = make_adapter({})

    with warnings.catch_warnings(record=True) as _w:
        result = adapter.get_export_fmt("none")

    assert result == []


def test_get_export_fmt_invalid_type_returns_empty():
    cfg = {"output": {"formats": "not-a-list-or-dict"}}
    adapter = ConfigAdapter(cfg)

    fmt = adapter.get_export_fmt("any")
    assert fmt == []


def test_get_plugins_config():
    cfg = {
        "plugins": {
            "enable_local_plugins": True,
            "local_plugins_path": "/tmp",
            "override_builtins": True,
        }
    }
    adapter = make_adapter(cfg)

    out = adapter.get_plugins_config()
    assert out["enable_local_plugins"] is True
    assert out["local_plugins_path"] == "/tmp"


def test_get_processor_configs_site_overrides():
    cfg = {
        "sites": {
            "s": {
                "processors": [
                    {"name": "clean", "overwrite": True, "x": 1},
                ]
            }
        },
        "plugins": {"processors": [{"name": "global", "overwrite": False}]},
    }
    adapter = make_adapter(cfg)
    procs = adapter.get_processor_configs("s")

    assert len(procs) == 1
    assert isinstance(procs[0], ProcessorConfig)
    assert procs[0].name == "clean"
    assert procs[0].overwrite is True
    assert procs[0].options["x"] == 1


def test_get_processor_configs_global():
    cfg = {"general": {"processors": [{"name": "global"}]}}
    adapter = make_adapter(cfg)
    procs = adapter.get_processor_configs("x")

    assert len(procs) == 1
    assert procs[0].name == "global"


def test_get_book_ids_scalar():
    adapter = make_adapter({"sites": {"s": {"book_ids": "123"}}})
    result = adapter.get_book_ids("s")
    assert result == [BookConfig(book_id="123")]


def test_get_book_ids_dict():
    adapter = make_adapter({"sites": {"s": {"book_ids": {"book_id": 123}}}})
    result = adapter.get_book_ids("s")
    assert result == [BookConfig(book_id="123")]


def test_get_book_ids_list_mixed():
    adapter = make_adapter({"sites": {"s": {"book_ids": ["1", 2, {"book_id": 3}]}}})
    result = adapter.get_book_ids("s")
    assert [cfg.book_id for cfg in result] == ["1", "2", "3"]


def test_get_book_ids_invalid_raises():
    adapter = make_adapter({"sites": {"s": {"book_ids": object()}}})
    with pytest.raises(ValueError):
        adapter.get_book_ids("s")


def test_get_book_ids_invalid_item():
    adapter = make_adapter({"sites": {"s": {"book_ids": [None]}}})
    with pytest.raises(ValueError):
        adapter.get_book_ids("s")


def test_get_config():
    cfg = {"general": {"x": 1}, "sites": {"s1": {}}}
    adapter = ConfigAdapter(cfg)
    assert adapter.get_config() == cfg


def test_get_log_level_specific():
    cfg = {"general": {"debug": {"log_level": "ERROR"}}}
    adapter = ConfigAdapter(cfg)
    assert adapter.get_log_level() == "ERROR"


def test_get_log_level_debug_no_level():
    cfg = {"general": {"debug": {}}}
    adapter = ConfigAdapter(cfg)
    assert adapter.get_log_level() == "INFO"


def test_get_log_level_no_debug():
    cfg = {"general": {}}
    adapter = ConfigAdapter(cfg)
    assert adapter.get_log_level() == "INFO"


def test_get_log_level_no_general():
    adapter = ConfigAdapter({})
    assert adapter.get_log_level() == "INFO"


def test_dict_to_book_cfg_basic():
    out = ConfigAdapter._dict_to_book_cfg({"book_id": 1})
    assert out.book_id == "1"


def test_dict_to_book_cfg_missing():
    with pytest.raises(ValueError):
        ConfigAdapter._dict_to_book_cfg({})


def test_dict_to_book_cfg_ignore_ids():
    out = ConfigAdapter._dict_to_book_cfg({"book_id": 1, "ignore_ids": ["1", 2, "3"]})
    assert out.ignore_ids == frozenset({"1", "2", "3"})


def test_dict_to_ocr_cfg_basic():
    out = ConfigAdapter._dict_to_ocr_cfg({"precision": "fp16"})
    assert isinstance(out, OCRConfig)
    assert out.precision == "fp16"


def test_dict_to_ocr_cfg_not_dict():
    out = ConfigAdapter._dict_to_ocr_cfg("xx")
    assert isinstance(out, OCRConfig)


def test_to_processor_cfgs_non_list_returns_empty():
    result = ConfigAdapter._to_processor_cfgs("not-a-list")
    assert result == []


def test_to_processor_cfgs_skip_non_dict():
    data = [
        {"name": "valid"},
        "not-a-dict",  # should trigger continue
        123,  # should also trigger continue
    ]

    result = ConfigAdapter._to_processor_cfgs(data)
    assert len(result) == 1
    assert result[0].name == "valid"


def test_to_processor_cfgs_skip_empty_name():
    data = [
        {"name": ""},  # should skip
        {"name": "   "},  # should skip (strip -> "")
        {"other": "x"},  # no name -> skip
        {"name": "clean", "x": 1},  # valid one
    ]

    result = ConfigAdapter._to_processor_cfgs(data)
    assert len(result) == 1
    assert result[0].name == "clean"
    assert result[0].options == {"x": 1}


def test_convert_fmt_dict_warns():
    with warnings.catch_warnings(record=True) as w:
        result = ConfigAdapter._convert_fmt_dict({"make_txt": True, "make_x": False})

    assert result == ["txt"]
    assert any("legacy" in str(wi.message) for wi in w)


def test_get_log_dir_specific(tmp_path):
    cfg = {"general": {"debug": {"log_dir": str(tmp_path / "mylogs")}}}
    adapter = ConfigAdapter(cfg)
    out = adapter.get_log_dir()

    assert isinstance(out, Path)
    assert out == (tmp_path / "mylogs").resolve()


def test_get_log_dir_default(tmp_path, monkeypatch):
    # change cwd so "./logs" is predictable
    monkeypatch.chdir(tmp_path)

    adapter = ConfigAdapter({"general": {}})
    result = adapter.get_log_dir()

    assert result == (tmp_path / "logs").resolve()


def test_get_log_dir_expand_user(monkeypatch, tmp_path):
    user_logs = tmp_path / "expanded_logs"

    if os.name == "nt":  # Windows
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
    else:  # Linux/macOS
        monkeypatch.setenv("HOME", str(tmp_path))

    cfg = {"general": {"debug": {"log_dir": "~/expanded_logs"}}}
    adapter = ConfigAdapter(cfg)
    out = adapter.get_log_dir()

    assert out == user_logs.resolve()


def test_get_log_dir_invalid_type_fallback():
    cfg = {"general": {"debug": {"log_dir": 123}}}
    adapter = ConfigAdapter(cfg)

    with pytest.raises(TypeError):
        adapter.get_log_dir()
