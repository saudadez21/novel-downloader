from novel_downloader.libs.textutils.truncate import (
    content_prefix,
    truncate_half_lines,
)

# -------------------------------------------------------------
# Tests for content_prefix
# -------------------------------------------------------------


def test_content_prefix_basic():
    assert content_prefix("abcdef", 3) == "abc"
    assert content_prefix("abcdef", 6) == "abcdef"
    assert content_prefix("abcdef", 10) == "abcdef"


def test_content_prefix_ignore_chars():
    text = "a b c d e"
    ignore = {" "}

    # Ignoring spaces, want 3 visible characters
    assert content_prefix(text, 3, ignore) == "a b c"


def test_content_prefix_ignore_and_normal_chars():
    text = "a,b,c,d"
    ignore = {","}
    assert content_prefix(text, 3, ignore) == "a,b,c"


def test_content_prefix_empty_string():
    assert content_prefix("", 5) == ""
    assert content_prefix("", 0) == ""


def test_content_prefix_n_zero():
    assert content_prefix("abcdef", 0) == ""  # zero content chars -> empty


def test_content_prefix_no_ignored_chars():
    assert content_prefix("abc", 2, ignore_chars=set()) == "ab"


def test_content_prefix_unicode():
    text = "你 好 世 界"
    ignore = {" "}
    assert content_prefix(text, 2, ignore) == "你 好"


# -------------------------------------------------------------
# Tests for truncate_half_lines
# -------------------------------------------------------------


def test_truncate_half_lines_basic():
    txt = "a\nb\nc\nd\n"
    # non-empty lines = 4 -> keep first 2
    assert truncate_half_lines(txt) == "a\nb"


def test_truncate_half_lines_odd():
    txt = "a\nb\nc\n"
    # 3 non-empty lines -> keep ceil(3/2) = 2
    assert truncate_half_lines(txt) == "a\nb"


def test_truncate_half_lines_with_empty_lines():
    txt = "a\n\nb\n\nc\n\n\n"
    # non-empty lines: a, b, c -> keep 2
    assert truncate_half_lines(txt) == "a\nb"


def test_truncate_half_lines_all_empty():
    txt = "\n\n   \n\n"
    # non-empty lines = 0 -> keep 0 -> return ""
    assert truncate_half_lines(txt) == ""


def test_truncate_half_lines_single_line():
    txt = "hello"
    assert truncate_half_lines(txt) == "hello"


def test_truncate_half_lines_unicode():
    txt = "你好\n世界\n测试\n中文"
    # 4 lines -> keep 2
    assert truncate_half_lines(txt) == "你好\n世界"
