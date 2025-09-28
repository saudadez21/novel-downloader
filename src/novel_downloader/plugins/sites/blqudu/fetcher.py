#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.blqudu.fetcher
---------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class BlquduSession(GenericSession):
    """
    A session class for interacting with the 笔趣读 (www.blqudu.cc) novel.
    """

    site_name: str = "blqudu"

    BOOK_INFO_URL = "https://www.blqudu.cc/{book_id}/"
    CHAPTER_URL = "https://www.biqudv.cc/{book_id}/{chapter_id}.html"
