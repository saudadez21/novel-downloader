#!/usr/bin/env python3
"""
novel_downloader.models.search
------------------------------

"""

from typing import TypedDict


class SearchResult(TypedDict, total=True):
    site: str
    book_id: str
    title: str
    author: str
    latest_chapter: str
    update_date: str
    word_count: str
    priority: int
