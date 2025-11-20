import json
from pathlib import Path

import pytest
from novel_downloader.infra.config.file_io import (
    _load_by_extension,
    _resolve_file_path,
    _validate_dict,
    copy_default_config,
    get_config_value,
    load_config,
    save_config,
    save_config_file,
)

# ------------------------------------
# _resolve_file_path
# ------------------------------------


def test_resolve_user_path_first_priority(tmp_path):
    user_file = tmp_path / "myconfig.json"
    user_file.write_text("{}", encoding="utf-8")

    result = _resolve_file_path(user_file, [], Path("nope"))
    assert result == user_file.resolve()


def test_resolve_user_path_not_found_logs_warning(tmp_path, caplog):
    missing = tmp_path / "missing.json"

    result = _resolve_file_path(missing, [], tmp_path / "fallback.toml")
    assert result is None or isinstance(result, Path)
    assert "Specified file not found" in caplog.text


def test_resolve_local_fallback(tmp_path, monkeypatch):
    local_file = tmp_path / "settings.json"
    local_file.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    result = _resolve_file_path(None, ["settings.json"], Path("nope"))
    assert result == local_file.resolve()


def test_resolve_global_fallback(tmp_path):
    fallback = tmp_path / "fallback.toml"
    fallback.write_text('name = "x"', encoding="utf-8")

    result = _resolve_file_path(None, [], fallback)
    assert result == fallback.resolve()


def test_resolve_no_matches_returns_none(tmp_path):
    result = _resolve_file_path(None, [], tmp_path / "not_exists.json")
    assert result is None


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
# save_config
# ------------------------------------


def test_save_config(tmp_path):
    out = tmp_path / "out.json"
    save_config({"a": 1}, out)
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1}


def test_save_config_error(tmp_path, monkeypatch, caplog):
    out = tmp_path / "dir" / "out.json"

    # Simulate failing write
    def bad_open(*args, **kwargs):
        raise OSError("can't write")

    monkeypatch.setattr(Path, "open", bad_open)

    with pytest.raises(OSError):
        save_config({"a": 1}, out)

    assert "Failed to write config JSON" in caplog.text


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


# ------------------------------------
# save_config_file
# ------------------------------------


def test_save_config_file_json(tmp_path):
    src = tmp_path / "input.json"
    out = tmp_path / "output.json"
    src.write_text('{"a": 1}', encoding="utf-8")

    save_config_file(src, out)
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1}


def test_save_config_file_missing(tmp_path):
    src = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        save_config_file(src, tmp_path / "x.json")
