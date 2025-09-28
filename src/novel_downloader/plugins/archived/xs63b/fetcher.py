#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xs63b.fetcher
-----------------------------------------------

"""

import asyncio
import base64
import re
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession


class Xs63bSession(BaseSession):
    """
    A session class for interacting with the 小说路上 (m.xs63b.com) novel.
    """

    site_name: str = "xs63b"

    BOOK_INFO_URL = "https://m.xs63b.com/{book_id}/"
    BOOK_CATALOG_URL = "https://www.xs63b.com/{book_id}/"
    CHAPTER_URL = "https://m.xs63b.com/{book_id}/{chapter_id}.html"

    _JSARR_PATTERN = re.compile(r"var\s+jsarr\s*=\s*\[([^\]]+)\]")
    _JSSTR_PATTERN = re.compile(r"var\s+jsstr\s*=\s*\"([^\"]+)\";")

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
                    "xs63b get_book_chapter(%s) failed: %s",
                    chapter_url,
                    exc,
                )
                return []

            html_pages.append(html)
            if "/xs635/mobile/images/nextpage.png" not in html:
                break

            jsarr = self._parse_jsarr(html)
            jsstr = self._parse_jsstr(html)
            chapter_url = self._build_chapter_url(book_id, jsarr, jsstr)

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
