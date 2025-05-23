#!/usr/bin/env python3
"""
tests.utils.text_utils.test_text_cleaning
----------------------------------------------

Unit tests for the `clean_chapter_title` and `is_promotional_line` functions,
which strip bracketed promo content and detect promotional/ad-like lines.
"""

from novel_downloader.utils.text_utils import text_cleaning


def test_clean_chapter_title_no_blacklisted():
    """Title without blacklisted words in brackets should remain unchanged."""
    title = "Chapter 1 (Introduction)"
    assert text_cleaning.clean_chapter_title(title) == "Chapter 1 (Introduction)"


def test_clean_chapter_title_remove_blacklisted(monkeypatch):
    """Bracketed sections containing blacklisted words should be removed."""
    # Monkeypatch the blacklist to a known test set
    monkeypatch.setattr(text_cleaning, "_BLACKLISTED_WORDS", {"spam", "ad"})
    title = "Title (spam offer) after"
    # Only the "(spam offer)" part should be stripped
    assert text_cleaning.clean_chapter_title(title) == "Title  after".strip()


def test_clean_chapter_title_multiple_brackets(monkeypatch):
    """Only bracketed sections with blacklisted words are removed, others stay."""
    monkeypatch.setattr(text_cleaning, "_BLACKLISTED_WORDS", {"x"})
    title = "Intro (keep) middle (x remove) end"
    # "(keep)" stays, "(x remove)" is removed
    assert (
        text_cleaning.clean_chapter_title(title) == "Intro (keep) middle  end".strip()
    )


def test_is_promotional_line_blacklisted(monkeypatch):
    """Lines containing any blacklisted keyword should be flagged."""
    monkeypatch.setattr(text_cleaning, "_BLACKLISTED_WORDS", {"promo"})
    line = "This has a Promo inside"
    assert text_cleaning.is_promotional_line(line) is True


def test_is_promotional_line_k_pattern():
    """Lines matching the '\\d{1,4}k' pattern should be flagged."""
    line = "Readership: 1234k"
    assert text_cleaning.is_promotional_line(line) is True


def test_is_promotional_line_clean(monkeypatch):
    """Lines without promos or 'k' counts should not be flagged."""
    monkeypatch.setattr(text_cleaning, "_BLACKLISTED_WORDS", {"spam"})
    line = "Just a normal content line."
    assert text_cleaning.is_promotional_line(line) is False
