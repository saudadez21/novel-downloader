#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.n71ge
------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["71ge", "n71ge"],
)
class N71geSession(BaseSession):
    """
    A session class for interacting with the 新吾爱文学 (www.71ge.com) novel website.
    """

    site_name: str = "n71ge"

    BOOK_INFO_URL = "https://www.71ge.com/{book_id}/"
    CHAPTER_URL = "https://www.71ge.com/{book_id}/{chapter_id}.html"

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
        """
        Fetch the raw HTML of a single chapter asynchronously.

        Order: [page1, ..., pageN]

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        html_pages: list[str] = []
        idx = 1
        suffix = chapter_id

        while True:
            url = self.chapter_url(book_id, suffix)
            try:
                html = await self.fetch(url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "n71ge get_book_chapter(%s page %d) failed: %s",
                    chapter_id,
                    idx,
                    exc,
                )
                return []

            html_pages.append(html)

            next_suffix = f"{chapter_id}_{idx + 1}"
            if f"{next_suffix}.html" not in html:
                break

            suffix = next_suffix
            idx += 1
            await self._sleep()

        return html_pages

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
