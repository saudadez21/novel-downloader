#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.common.session
---------------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.models import FetcherConfig, SiteProfile


class CommonSession(BaseSession):
    """
    A common async session for handling site-specific HTTP requests.
    """

    def __init__(
        self,
        site: str,
        profile: SiteProfile,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(site, config, cookies, **kwargs)
        self._profile = profile

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as a string.
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
        :return: The chapter content as a string.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

    def book_info_url(self, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return self._profile["book_info_url"].format(book_id=book_id)

    def chapter_url(self, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return self._profile["chapter_url"].format(
            book_id=book_id, chapter_id=chapter_id
        )
