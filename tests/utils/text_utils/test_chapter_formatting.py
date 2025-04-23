#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.text_utils.test_chapter_formatting
----------------------------------------------

Unit tests for the `format_chapter` function, which formats chapter content by
combining the title, paragraph blocks, and optional author notes into a single
structured string output.
"""

from novel_downloader.utils.text_utils.chapter_formatting import format_chapter


def test_format_chapter_without_author():
    """Test formatting with title and paragraphs, no author_say."""
    title = "  Chapter 1  "
    paragraphs = "\nLine1\n\nLine2\n  \n"
    expected = "Chapter 1\n\nLine1\n\nLine2"
    result = format_chapter(title, paragraphs)
    assert result == expected


def test_format_chapter_with_author():
    """Test formatting with title, paragraphs, and a multi-line author_say."""
    title = "Title"
    paragraphs = "Para1\nPara2"
    author_say = "\nNote1\n\nNote2\n"
    expected = "\n\n".join(
        [
            "Title",
            "Para1",
            "Para2",
            "---",
            "作者说:",
            "Note1",
            "Note2",
        ]
    )
    result = format_chapter(title, paragraphs, author_say=author_say)
    assert result == expected


def test_format_chapter_empty_paragraphs():
    """
    Test that only title is returned when paragraphs string is empty or whitespace
    """
    title = " Only Title "
    paragraphs = "   \n  \n"
    expected = "Only Title"
    result = format_chapter(title, paragraphs)
    assert result == expected


def test_format_chapter_no_paragraphs_but_author():
    """Test that author_say is still added even if no paragraphs are present."""
    title = "T"
    paragraphs = ""
    author_say = "Author note"
    expected = "\n\n".join(
        [
            "T",
            "---",
            "作者说:",
            "Author note",
        ]
    )
    result = format_chapter(title, paragraphs, author_say=author_say)
    assert result == expected
