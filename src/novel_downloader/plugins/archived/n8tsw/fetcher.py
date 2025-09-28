#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.n8tsw.fetcher
-----------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession


class N8tswSession(GenericSession):
    """
    A session class for interacting with the 笔趣阁 (www.8tsw.com) novel.
    """

    site_name: str = "n8tsw"

    BOOK_INFO_URL = "https://www.8tsw.com/{book_id}/"
    CHAPTER_URL = "https://www.8tsw.com/{book_id}/{chapter_id}.html"
