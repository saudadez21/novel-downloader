#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.mangg_net
----------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["mangg_net"],
)
class ManggNetSession(BaseSession):
    """
    A session class for interacting with the 追书网 (www.mangg.net) novel.
    """

    site_name: str = "mangg_net"

    BASE_URL = "https://www.mangg.net"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [page1, ..., pageN]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        book_id = book_id.replace("-", "/")
        html_pages: list[str] = []
        idx = 1
        suffix = self.relative_info_url(book_id, idx)

        while True:
            full_url = self.BASE_URL + suffix
            try:
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "%s get_book_info(%s page %d) failed: %s",
                    self.site_name,
                    book_id,
                    idx,
                    exc,
                )
                return []

            html_pages.append(html)
            idx += 1
            suffix = self.relative_info_url(book_id, idx)
            if suffix not in html:
                break
            await self._sleep()

        return html_pages

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
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/index_{idx}.html" if idx > 1 else f"/{book_id}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/{book_id}/{chapter_id}.html"
        )
