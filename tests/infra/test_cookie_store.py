import json

from novel_downloader.infra.cookies import CookieStore

# -----------------------------------------------------
# parse file cases in CookieStore.load_all
# -----------------------------------------------------


def test_cookie_store_load_nonexistent_files(tmp_path):
    """If no cookie files exist -> cache stays empty"""
    store = CookieStore(tmp_path)
    store.load_all()
    assert store.cache == {}


def test_cookie_store_load_valid_single_file(tmp_path):
    """Load one correct cookie file."""
    f = tmp_path / "aiohttp.cookies"
    f.write_text(
        json.dumps(
            [
                {"name": "token", "value": "abc"},
                {"name": "uid", "value": "123"},
            ]
        ),
        encoding="utf-8",
    )

    store = CookieStore(tmp_path)
    store.load_all()

    assert store.cache == {"token": "abc", "uid": "123"}


def test_cookie_store_multiple_files_merge(tmp_path):
    """CookieStore merges values from multiple cookie files."""
    f1 = tmp_path / "aiohttp.cookies"
    f1.write_text(json.dumps([{"name": "a", "value": "1"}]), encoding="utf-8")

    f2 = tmp_path / "httpx.cookies"
    f2.write_text(json.dumps([{"name": "b", "value": "2"}]), encoding="utf-8")

    store = CookieStore(tmp_path)
    store.load_all()

    assert store.cache == {"a": "1", "b": "2"}


def test_cookie_store_skip_invalid_entries(tmp_path):
    """Entries missing name or value must be ignored."""
    f = tmp_path / "aiohttp.cookies"
    f.write_text(
        json.dumps(
            [
                {"name": "a"},  # missing value
                {"value": "x"},  # missing name
                {"name": "ok", "value": "1"},
            ]
        ),
        encoding="utf-8",
    )

    store = CookieStore(tmp_path)
    store.load_all()

    assert store.cache == {"ok": "1"}


def test_cookie_store_invalid_json_skipped(tmp_path):
    """Invalid JSON -> JSONDecodeError -> silently skip file."""
    f = tmp_path / "curl_cffi.cookies"
    f.write_text("{not-valid-json", encoding="utf-8")

    store = CookieStore(tmp_path)
    store.load_all()  # should not crash

    assert store.cache == {}


def test_cookie_store_io_error_skipped(tmp_path, monkeypatch):
    """json parsing error must be caught and skipped."""
    f = tmp_path / "aiohttp.cookies"
    f.write_text("[]", encoding="utf-8")

    # monkeypatch json.loads to raise JSONDecodeError
    def bad_loads(*a, **k):
        raise json.JSONDecodeError("bad", "x", 0)

    monkeypatch.setattr(json, "loads", bad_loads)

    store = CookieStore(tmp_path)
    store.load_all()  # must NOT crash

    assert store.cache == {}  # skipped due to error


# -----------------------------------------------------
# mtime caching
# -----------------------------------------------------


def test_cookie_store_mtime_no_reload(tmp_path):
    """
    If file mtime does not change, load_all should not reload content.
    """
    f = tmp_path / "aiohttp.cookies"
    f.write_text('[{"name": "a", "value": "1"}]', encoding="utf-8")

    store = CookieStore(tmp_path)

    # First load -> fills cache
    store.load_all()
    assert store.cache == {"a": "1"}

    # save mtime
    real_mtime = f.stat().st_mtime

    # Clear cache
    store.cache.clear()

    # Pretend file mtime didn't change
    store.mtimes["aiohttp.cookies"] = real_mtime

    # Now load_all should SKIP loading (mtime match)
    store.load_all()

    assert store.cache == {}


def test_cookie_store_get(tmp_path):
    """
    get() should load cookies and return matching value or "" for missing.
    """
    f = tmp_path / "aiohttp.cookies"
    f.write_text(json.dumps([{"name": "token", "value": "xyz"}]), encoding="utf-8")

    store = CookieStore(tmp_path)

    assert store.get("token") == "xyz"
    assert store.get("missing") == ""
