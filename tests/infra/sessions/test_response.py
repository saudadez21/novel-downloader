import pytest
from novel_downloader.infra.sessions.response import BaseResponse, Headers

# ---------------------------------------------------------
# Headers tests
# ---------------------------------------------------------


def test_headers_init_from_mapping():
    h = Headers({"Content-Type": "text/html", "X-Test": "1"})
    assert h["content-type"] == "text/html"
    assert h["x-test"] == "1"
    assert "content-type" in h
    assert "Content-Type" in h


def test_headers_init_from_sequence():
    h = Headers([("Content-Type", "text/html"), ("X-Test", "1")])
    assert h["content-type"] == "text/html"
    assert h.get_all("x-test") == ["1"]


def test_headers_add_multiple_values():
    h = Headers()
    h.add("Set-Cookie", "a=1")
    h.add("Set-Cookie", "b=2")

    all_cookies = h.get_all("set-cookie")
    assert all_cookies == ["a=1", "b=2"]
    assert h["set-cookie"] == "a=1"  # first one


def test_headers_setitem_overwrites():
    h = Headers()
    h.add("X-Test", "a")
    h.add("X-Test", "b")

    h["X-Test"] = "final"

    assert h.get_all("x-test") == ["final"]


def test_headers_delete():
    h = Headers({"A": "1"})
    del h["a"]
    assert "a" not in h


def test_headers_repr():
    h = Headers({"A": "1", "B": "2"})
    r = repr(h)
    # something like <Headers (a=1, b=1)>
    assert r.startswith("<Headers")
    assert "a=" in r
    assert "b=" in r


def test_headers_getitem_keyerror():
    h = Headers()
    with pytest.raises(KeyError):
        _ = h["missing"]


def test_headers_iter_and_len():
    h = Headers({"A": "1", "B": "2"})
    keys = list(iter(h))
    assert set(keys) == {"a", "b"}
    assert len(h) == 2


def test_headers_contains_non_string():
    h = Headers({"A": "1"})
    assert ("A" in h) is True
    assert (123 in h) is False
    assert (None in h) is False


# ---------------------------------------------------------
# BaseResponse tests
# ---------------------------------------------------------


def test_base_response_basic_text_utf8():
    resp = BaseResponse(
        content="hello 世界".encode(),
        headers={"Content-Type": "text/plain"},
        status=200,
        encoding="utf-8",
    )
    assert resp.text == "hello 世界"
    assert resp.ok


def test_base_response_encoding_fallback_gbk():
    gbk_bytes = "你好，世界".encode("gbk")
    resp = BaseResponse(content=gbk_bytes, encoding="utf-8")
    assert resp.text == "你好，世界"  # fallback should decode it


def test_base_response_invalid_bytes_fallback():
    resp = BaseResponse(content=b"\xff\xfe\xfa", encoding="utf-8")
    assert isinstance(resp.text, str)


def test_base_response_json():
    resp = BaseResponse(content=b'{"a": 1}', encoding="utf-8")
    assert resp.json() == {"a": 1}


def test_base_response_json_invalid():
    resp = BaseResponse(content=b"not-json", encoding="utf-8")
    with pytest.raises(ValueError):
        resp.json()


def test_base_response_ok_property():
    assert BaseResponse(content=b"", status=200).ok is True
    assert BaseResponse(content=b"", status=399).ok is True
    assert BaseResponse(content=b"", status=400).ok is False
    assert BaseResponse(content=b"", status=500).ok is False


def test_base_response_repr():
    resp = BaseResponse(content=b"abcd", status=201)
    r = repr(resp)
    assert "<BaseResponse" in r
    assert "status=201" in r
    assert "len=4" in r
