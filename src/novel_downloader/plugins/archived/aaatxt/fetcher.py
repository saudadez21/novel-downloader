#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.aaatxt.fetcher
------------------------------------------------

"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class AaatxtFetcher(GenericFetcher):
    """
    A session class for interacting with the 3A电子书 (www.aaatxt.com) novel.
    """

    site_name: str = "aaatxt"

    BOOK_INFO_URL = "http://www.aaatxt.com/shu/{book_id}.html"
    CHAPTER_URL = "http://www.aaatxt.com/yuedu/{chapter_id}.html"

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(chapter_id=chapter_id)
        return [await self.fetch(url, encoding="gb2312", **kwargs)]
