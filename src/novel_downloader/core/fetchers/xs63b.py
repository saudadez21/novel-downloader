#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.xs63b
------------------------------------

"""

import asyncio
import base64
import re
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig
from novel_downloader.utils import async_jitter_sleep


@register_fetcher(
    site_keys=["xs63b"],
)
class Xs63bSession(BaseSession):
    """
    A session class for interacting with the 小说路上 (m.xs63b.com) novel website.
    """

    BOOK_INFO_URL = "https://m.xs63b.com/{book_id}/"
    BOOK_CATALOG_URL = "https://www.xs63b.com/{book_id}/"
    CHAPTER_URL = "https://m.xs63b.com/{book_id}/{chapter_id}.html"

    _JSARR_PATTERN = re.compile(r"var\s+jsarr\s*=\s*\[([^\]]+)\]")
    _JSSTR_PATTERN = re.compile(r"var\s+jsstr\s*=\s*\"([^\"]+)\";")

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("xs63b", config, cookies, **kwargs)

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [info, catalog]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        book_id = book_id.replace("-", "/")
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        info_html, catalog_html = await asyncio.gather(
            self.fetch(info_url, ssl=False, **kwargs),
            self.fetch(catalog_url, ssl=False, **kwargs),
        )
        return [info_html, catalog_html]

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
        chapter_url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)

        while True:
            try:
                html = await self.fetch(chapter_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "[async] get_book_chapter(%s page %d) failed: %s",
                    chapter_url,
                    exc,
                )
                break

            html_pages.append(html)
            if "/xs635/mobile/images/nextpage.png" not in html:
                break

            jsarr = self._parse_jsarr(html)
            jsstr = self._parse_jsstr(html)
            chapter_url = self._build_chapter_url(book_id, jsarr, jsstr)

            await async_jitter_sleep(
                self.request_interval,
                mul_spread=1.1,
                max_sleep=self.request_interval + 2,
            )

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
    def book_catalog_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog page URL.
        """
        return cls.BOOK_CATALOG_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    @classmethod
    def _parse_jsarr(cls, text: str) -> list[int]:
        """
        Extract jsarr from `var jsarr = [...];`.

        Raises ValueError if not found.
        """
        m = cls._JSARR_PATTERN.search(text)
        if not m:
            raise ValueError("jsarr not found")
        return [int(x) for x in m.group(1).split(",")]

    @classmethod
    def _parse_jsstr(cls, text: str) -> str:
        """
        Extract jsstr from `var jsstr = "...";`.

        Raises ValueError if not found.
        """
        m = cls._JSSTR_PATTERN.search(text)
        if not m:
            raise ValueError("jsstr not found")
        return m.group(1)

    @staticmethod
    def _build_chapter_url(book_id: str, jsarr: list[int], jsstr: str) -> str:
        decoded = base64.b64decode(jsstr).decode("utf-8")
        nnarr = list(decoded)
        nnstr = "".join(nnarr[i] for i in jsarr)
        return f"https://m.xs63b.com/{book_id}/{nnstr}.html"
