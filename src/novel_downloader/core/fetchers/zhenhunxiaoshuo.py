#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.zhenhunxiaoshuo
----------------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["zhenhunxiaoshuo"],
)
class ZhenhunxiaoshuoSession(BaseSession):
    """
    A session class for interacting with the 镇魂小说网
    (www.zhenhunxiaoshuo.com) novel.
    """

    site_name: str = "zhenhunxiaoshuo"

    BOOK_INFO_URL = "https://www.zhenhunxiaoshuo.com/{book_id}/"
    CHAPTER_URL = "https://www.zhenhunxiaoshuo.com/{chapter_id}.html"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(chapter_id=chapter_id)
