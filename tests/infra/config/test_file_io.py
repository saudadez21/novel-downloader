from pathlib import Path

import pytest

from novel_downloader.infra.config.file_io import (
    _load_by_extension,
    _resolve_file_path,
    _validate_dict,
    copy_default_config,
    get_config_value,
    load_config,
)

# ------------------------------------
# _resolve_file_path
# ------------------------------------


def test_resolve_user_path_first_priority(tmp_path):
    user_file = tmp_path / "myconfig.json"
    user_file.write_text("{}", encoding="utf-8")

    result = _resolve_file_path(user_file, [])
    assert result == user_file.resolve()


def test_resolve_user_path_not_found_logs_warning(tmp_path, caplog):
    missing = tmp_path / "missing.json"

    result = _resolve_file_path(missing, [])
    assert result is None or isinstance(result, Path)
    assert "Specified file not found" in caplog.text


# ------------------------------------
# _validate_dict
# ------------------------------------


def test_validate_dict_success(tmp_path):
    path = tmp_path / "x.json"
    assert _validate_dict({"a": 1}, path, "json") == {"a": 1}


def test_validate_dict_failure_logs_warning(tmp_path, caplog):
    path = tmp_path / "bad.json"
    result = _validate_dict("not a dict", path, "json")
    assert result == {}
    assert "JSON content is not a dictionary" in caplog.text


# ------------------------------------
# _load_by_extension
# ------------------------------------


def test_load_json_ok(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert _load_by_extension(p) == {"a": 1}


def test_load_json_invalid(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_by_extension(p)


def test_load_toml_ok(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("a = 1\n", encoding="utf-8")
    assert _load_by_extension(p) == {"a": 1}


def test_load_toml_invalid(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("a = ", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_by_extension(p)


def test_load_by_extension_unsupported(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("x: 1", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_by_extension(p)


# ------------------------------------
# load_config
# ------------------------------------


def test_load_config_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_config(None)


def test_load_config_from_local_json(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"x": 1}', encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    result = load_config(None)
    assert result == {"x": 1}


# ------------------------------------
# get_config_value
# ------------------------------------


def test_get_config_value_ok(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"db": {"port": 3306}}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert get_config_value(["db", "port"], 0) == 3306


def test_get_config_value_wrong_type(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"db": {"port": "oops"}}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert get_config_value(["db", "port"], 0) == 0


def test_get_config_value_missing(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"db": {}}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert get_config_value(["db", "host"], "localhost") == "localhost"


def test_get_config_value_intermediate_not_dict(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"db": {"port": "not_dict"}}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert get_config_value(["db", "port", "x"], 42) == 42


def test_get_config_value_empty_keys(tmp_path, monkeypatch):
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"a": 1}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert get_config_value([], "default") == "default"


# ------------------------------------
# copy_default_config
# ------------------------------------


def test_copy_default_config(tmp_path, monkeypatch):
    # Mock DEFAULT_CONFIG_FILE
    fake_default = tmp_path / "fake_default.toml"
    fake_default.write_text("x = 1", encoding="utf-8")

    monkeypatch.setattr(
        "novel_downloader.infra.config.file_io.DEFAULT_CONFIG_FILE",
        fake_default,
    )

    out = tmp_path / "copy" / "target.toml"
    copy_default_config(out)

    assert out.read_text(encoding="utf-8") == "x = 1"
