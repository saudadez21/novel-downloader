#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.quanben5
---------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig


@register_fetcher(
    site_keys=["quanben5"],
)
class Quanben5Session(BaseSession):
    """
    A session class for interacting with the 全本小说网 (quanben5.com) novel website.
    """

    BOOK_INFO_URL = "https://{base_url}/n/{book_id}/xiaoshuo.html"
    CHAPTER_URL = "https://{base_url}/n/{book_id}/{chapter_id}.html"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("quanben5", config, cookies, **kwargs)
        self.base_url = (
            "quanben5.com"
            if config.locale_style == "simplified"
            else "big5.quanben5.com"
        )

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        url = self.book_info_url(base_url=self.base_url, book_id=book_id)
        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        url = self.chapter_url(
            base_url=self.base_url, book_id=book_id, chapter_id=chapter_id
        )
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def book_info_url(cls, base_url: str, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(base_url=base_url, book_id=book_id)

    @classmethod
    def chapter_url(cls, base_url: str, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(
            base_url=base_url, book_id=book_id, chapter_id=chapter_id
        )
