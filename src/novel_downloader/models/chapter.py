#!/usr/bin/env python3
"""
novel_downloader.models.chapter
-------------------------------

"""

from typing import Any, TypedDict


class ChapterDict(TypedDict, total=True):
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
