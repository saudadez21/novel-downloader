#!/usr/bin/env python3
"""
novel_downloader.schemas.search
-------------------------------

"""

from typing import TypedDict


class SearchResult(TypedDict, total=True):
    site: str
    book_id: str
    book_url: str
    cover_url: str
    title: str
    author: str
    latest_chapter: str
    update_date: str
    word_count: str
    priority: int
