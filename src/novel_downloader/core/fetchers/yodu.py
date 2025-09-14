#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.yodu
-----------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["yodu"],
)
class YoduSession(BaseSession):
    """
    A session class for interacting with the 有度中文网 (www.yodu.org) novel.
    """

    site_name: str = "yodu"

    BASE_URL = "https://www.yodu.org"
    BOOK_INFO_URL = "https://www.yodu.org/book/{book_id}/"

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
        suffix = self.relative_chapter_url(book_id, chapter_id, idx)

        while True:
            full_url = self.BASE_URL + suffix
            try:
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "%s get_book_chapter(%s page %d) failed: %s",
                    self.site_name,
                    book_id,
                    idx,
                    exc,
                )
                return []

            html_pages.append(html)
            idx += 1
            suffix = self.relative_chapter_url(book_id, chapter_id, idx)
            if suffix not in html:
                break
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
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )
