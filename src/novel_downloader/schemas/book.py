#!/usr/bin/env python3
"""
novel_downloader.schemas.book
-----------------------------

"""

from typing import Any, Literal, NotRequired, TypedDict

MediaType = Literal["image", "font", "css", "script", "audio", "other"]


class ChapterDict(TypedDict):
    id: str
    title: str
    content: str
    extra: dict[str, Any]


class MediaResource(TypedDict):
    type: MediaType
    paragraph_index: NotRequired[int]
    range: NotRequired[dict[str, int]]
    url: NotRequired[str]
    base64: NotRequired[str]
    mime: NotRequired[str]
    text: NotRequired[str]
    alt: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]


class ChapterInfoDict(TypedDict):
    title: str
    url: str
    chapterId: str
    accessible: NotRequired[bool]


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
    last_checked: NotRequired[float]  # Unix timestamp
