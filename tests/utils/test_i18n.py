#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_i18n
---------------------
"""

import importlib
import json
import sys

import pytest

import novel_downloader.utils.constants as const_mod
from novel_downloader.utils.state import state_mgr


@pytest.fixture(autouse=True)
def patch_locales_dir(tmp_path, monkeypatch):
    # 1) create an empty dir for our locale JSONs
    locale_dir = tmp_path / "locales"
    locale_dir.mkdir()

    # 2) patch the module constant so i18n picks up our temp dir
    monkeypatch.setattr(const_mod, "LOCALES_DIR", locale_dir)

    # 3) ensure we re‐import i18n from scratch in each test
    sys.modules.pop("novel_downloader.utils.i18n", None)

    return locale_dir


def load_i18n_module():
    # must invalidate caches so Python will re‐read the patched LOCALES_DIR
    importlib.invalidate_caches()
    return importlib.import_module("novel_downloader.utils.i18n")


def test_t_no_translations_returns_key(patch_locales_dir, monkeypatch):
    """With no JSON files present, t() should just return the key."""
    i18n = load_i18n_module()
    # make sure state_mgr.get_language() doesn't accidentally read your real state
    monkeypatch.setattr(state_mgr, "get_language", lambda: "zh")
    assert i18n.t("any_missing_key") == "any_missing_key"


def test_t_loads_and_prefers_current_language_and_fallback(
    patch_locales_dir, monkeypatch
):
    """
    - zh.json and en.json both exist
    - t() on 'zh' returns zh version
    - missing in zh => falls back to en
    - unsupported lang => falls back to en
    - missing in both => returns key
    """
    locale_dir = patch_locales_dir

    en_dict = {"hello": "Hello", "only_en": "EN"}
    zh_dict = {"hello": "你好"}

    (locale_dir / "en.json").write_text(json.dumps(en_dict), encoding="utf-8")
    (locale_dir / "zh.json").write_text(json.dumps(zh_dict), encoding="utf-8")

    i18n = load_i18n_module()

    # current = zh
    monkeypatch.setattr(state_mgr, "get_language", lambda: "zh")
    assert i18n.t("hello") == "你好"
    # 'only_en' missing in zh, should fallback to en
    assert i18n.t("only_en") == "EN"

    # current = fr (unsupported) => fallback to en
    monkeypatch.setattr(state_mgr, "get_language", lambda: "fr")
    assert i18n.t("hello") == "Hello"

    # missing in both => return key
    assert i18n.t("no_such_key") == "no_such_key"


def test_t_with_formatting_args(patch_locales_dir, monkeypatch):
    """Verify that {placeholders} in strings get formatted."""
    locale_dir = patch_locales_dir
    en_dict = {"welcome": "Welcome, {name}!"}
    (locale_dir / "en.json").write_text(json.dumps(en_dict), encoding="utf-8")

    i18n = load_i18n_module()
    monkeypatch.setattr(state_mgr, "get_language", lambda: "en")

    assert i18n.t("welcome", name="Alice") == "Welcome, Alice!"


def test_t_skips_malformed_json_and_uses_en_fallback(patch_locales_dir, monkeypatch):
    """
    If one locale file is syntactically invalid JSON, it is skipped entirely.
    Then t() with that language should still fall back to en.json.
    """
    locale_dir = patch_locales_dir

    # write a broken JSON
    (locale_dir / "xx.json").write_text("not valid json", encoding="utf-8")
    # write a valid en.json
    en_dict = {"foo": "Bar"}
    (locale_dir / "en.json").write_text(json.dumps(en_dict), encoding="utf-8")

    i18n = load_i18n_module()
    monkeypatch.setattr(state_mgr, "get_language", lambda: "xx")

    # 'foo' should resolve via English fallback
    assert i18n.t("foo") == "Bar"
    # anything else still returns the key
    assert i18n.t("does_not_exist") == "does_not_exist"
