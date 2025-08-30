#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.ttkan
------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig


@register_fetcher(
    site_keys=["ttkan"],
)
class TtkanSession(BaseSession):
    """
    A session class for interacting with the 天天看小说 (www.ttkan.co) novel website.
    """

    BOOK_INFO_URL = "https://{lang}.ttkan.co/novel/chapters/{book_id}"
    CHAPTER_URL = "https://{lang}.wa01.com/novel/pagea/{book_id}_{chapter_id}.html"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("ttkan", config, cookies, **kwargs)
        self._lang = "cn" if config.locale_style == "simplified" else "tw"

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
        url = self.book_info_url(book_id=book_id)
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
            book_id=book_id,
            chapter_id=chapter_id,
            lang=self._lang,
        )
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str, lang: str = "cn") -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :param lang: The language of the book. (cn / tw)
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id, lang=lang)

    @classmethod
    def chapter_url(
        cls,
        book_id: str,
        chapter_id: str,
        lang: str = "cn",
    ) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The chapter identifier.
        :param lang: The language of the book. (cn / tw)
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id, lang=lang)
