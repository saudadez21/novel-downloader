import pytest

from novel_downloader.infra.cookies import parse_cookies

# ---------------------------------------------------------------------
# Valid cases
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("a=1; b=2", {"a": "1", "b": "2"}),
        ("foo=bar;baz=qux", {"foo": "bar", "baz": "qux"}),
        ("x=1; y=2; z=3", {"x": "1", "y": "2", "z": "3"}),
        # extra spaces and trailing semicolon
        ("  a = 1 ; b= 2 ; ", {"a": "1", "b": "2"}),
        # empty key/value ignored
        ("=; a=1; =2", {"a": "1"}),
        # repeated keys: last one wins
        ("x=1; x=2", {"x": "2"}),
        # malformed part ignored
        ("x=1; invalid; y=2", {"x": "1", "y": "2"}),
    ],
)
def test_parse_cookies_from_string(input_str, expected):
    """String input should produce correct normalized dictionary."""
    assert parse_cookies(input_str) == expected


def test_parse_cookies_from_mapping():
    """Mapping input should be returned as a normalized dict."""
    cookies = {"A ": " 1 ", "B": "2"}
    result = parse_cookies(cookies)
    assert result == {"A": "1", "B": "2"}
    # Ensure new dict is returned
    assert result is not cookies


def test_parse_cookies_mixed_key_value_types():
    """Non-string keys and values should be converted to str."""
    cookies = {123: 456, "x": True}
    result = parse_cookies(cookies)
    assert result == {"123": "456", "x": "True"}


# ---------------------------------------------------------------------
# Invalid cases
# ---------------------------------------------------------------------


@pytest.mark.parametrize("bad_input", [123, 3.14, None, object(), [("a", "b")]])
def test_parse_cookies_invalid_type(bad_input):
    """Non-str and non-mapping inputs should raise TypeError."""
    with pytest.raises(TypeError, match="Unsupported cookie format"):
        parse_cookies(bad_input)
