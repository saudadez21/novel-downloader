#!/usr/bin/env python3
"""
novel_downloader.models.book
----------------------------

"""

from typing import Any, NotRequired, TypedDict


class ChapterDict(TypedDict):
    """
    TypedDict for a novel chapter.

    Fields:
        id      -- Unique chapter identifier
        title   -- Chapter title
        content -- Chapter text
        extra   -- Arbitrary metadata (e.g. author remarks, timestamps)
    """

    id: str
    title: str
    content: str
    extra: dict[str, Any]


class ChapterInfoDict(TypedDict):
    title: str
    url: str
    chapterId: str


class VolumeInfoDict(TypedDict):
    volume_name: str
    volume_cover: NotRequired[str]
    update_time: NotRequired[str]
    word_count: NotRequired[str]
    volume_intro: NotRequired[str]
    chapters: list[ChapterInfoDict]


class BookInfoDict(TypedDict):
    book_name: str
    author: str
    cover_url: str
    update_time: str
    summary: str
    extra: dict[str, Any]
    volumes: list[VolumeInfoDict]
    tags: NotRequired[list[str]]
    word_count: NotRequired[str]
    serial_status: NotRequired[str]
    summary_brief: NotRequired[str]
