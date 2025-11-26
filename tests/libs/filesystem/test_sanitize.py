import os

import pytest

from novel_downloader.libs.filesystem.sanitize import sanitize_filename

# ----------------------------------------------------------------------
# Common behavior (cross-platform)
# ----------------------------------------------------------------------


def test_empty_filename_becomes_untitled():
    assert sanitize_filename("") == "_untitled"


def test_strip_spaces_and_dots():
    assert sanitize_filename("  abc.txt  ") == "abc.txt"
    assert sanitize_filename(" abc. ") == "abc"


def test_posix_replaces_slash():
    # Always true on any OS
    assert sanitize_filename("a/b/c") == "a_b_c"


def test_max_length_cutting():
    name = "a" * 300 + ".txt"
    out = sanitize_filename(name, max_length=50)
    assert len(out) == 50
    assert out.endswith(".txt")


def test_max_length_no_extension():
    name = "x" * 300
    out = sanitize_filename(name, max_length=20)
    assert len(out) == 20


# ----------------------------------------------------------------------
# Windows-specific behavior
# ----------------------------------------------------------------------


@pytest.mark.skipif(os.name != "nt", reason="Windows-only tests")
class TestWindowsBehavior:
    def test_windows_illegal_chars_replaced(self):
        assert sanitize_filename('a<b>c:"d"|e?f*g.txt') == "a_b_c__d__e_f_g.txt"

    def test_windows_reserved_names_prefixed(self):
        assert sanitize_filename("CON.txt") == "_CON.txt"
        assert sanitize_filename("aux.TXT") == "_aux.TXT"

    def test_windows_trailing_space_dot_removed(self):
        assert sanitize_filename("abc. ") == "abc"
        assert sanitize_filename("abc...") == "abc"


# ----------------------------------------------------------------------
# POSIX-specific behavior
# ----------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only tests")
class TestPosixBehavior:
    def test_posix_illegal_slash_replaced(self):
        assert sanitize_filename("a/b/c.txt") == "a_b_c.txt"

    def test_posix_no_reserved_word_handling(self):
        assert sanitize_filename("CON.txt") == "CON.txt"
