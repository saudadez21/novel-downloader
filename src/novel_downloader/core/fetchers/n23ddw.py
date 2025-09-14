#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.n23ddw
-------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["n23ddw"],
)
class N23ddwSession(BaseSession):
    """
    A session class for interacting with the 顶点小说网 (www.23ddw.net) novel.
    """

    site_name: str = "n23ddw"

    BASE_URL = "https://www.23ddw.net"
    BOOK_INFO_URL = "https://www.23ddw.net/du/{book_id}/"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
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
        book_id = book_id.replace("-", "/")
        html_pages: list[str] = []
        idx = 1
        suffix = f"/du/{book_id}/{chapter_id}.html"

        while True:
            try:
                full_url = self.BASE_URL + suffix
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "n23ddw get_book_chapter(%s page %d) failed: %s",
                    chapter_id,
                    idx,
                    exc,
                )
                return []

            html_pages.append(html)

            idx += 1
            suffix = f"/du/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1 and suffix not in html:
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
