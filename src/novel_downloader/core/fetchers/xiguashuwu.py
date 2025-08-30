#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.xiguashuwu
-----------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig
from novel_downloader.utils import async_jitter_sleep


@register_fetcher(
    site_keys=["xiguashuwu"],
)
class XiguashuwuSession(BaseSession):
    """
    A session class for interacting with the 西瓜书屋 (www.xiguashuwu.com) novel.
    """

    BASE_URL = "https://www.xiguashuwu.com"
    BOOK_INFO_URL = "https://www.xiguashuwu.com/book/{book_id}/iszip/0/"
    BOOK_CATALOG_URL = "https://www.xiguashuwu.com/book/{book_id}/catalog/"
    CHAPTER_URL = "https://www.xiguashuwu.com/book/{book_id}/{chapter_id}.html"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("xiguashuwu", config, cookies, **kwargs)

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [info, catalogs1, ..., catalogsN]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        info_url = self.book_info_url(book_id=book_id)
        info_html = await self.fetch(info_url, **kwargs)

        catalog_url = self.book_catalog_url(book_id=book_id)
        catalog_pages: list[str] = []
        idx = 1
        while True:
            suffix = "" if idx == 1 else f"{idx}.html"
            full_url = catalog_url + suffix

            try:
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "[async] get_book_catalog(%s page %d) failed: %s",
                    book_id,
                    idx,
                    exc,
                )
                break

            catalog_pages.append(html)
            idx += 1
            next_patterns = [
                # f"javascript:readbook('{book_id}','{idx}');",
                # f"javascript:gobook('{book_id}','{idx}');",
                # f"javascript:runbook('{book_id}','{idx}');",
                # f"javascript:gotochapter('{book_id}','{idx}');",
                f"javascript:readbookjump('{book_id}','{idx}');",
                f"javascript:gobookjump('{book_id}','{idx}');",
                f"javascript:runbookjump('{book_id}','{idx}');",
                f"javascript:gotojump('{book_id}','{idx}');",
                f"javascript:gotochapterjump('{book_id}','{idx}');",
                f"/book/{book_id}/catalog/{idx}.html",
            ]
            if not any(pat in html for pat in next_patterns):
                break

            await async_jitter_sleep(
                self.request_interval,
                mul_spread=1.1,
                max_sleep=self.request_interval + 2,
            )
        return [info_html, *catalog_pages]

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

        while True:
            chapter_suffix = chapter_id if idx == 1 else f"{chapter_id}_{idx}"
            relative_path = self.relative_chapter_url(book_id, chapter_suffix)
            if idx > 1 and relative_path not in html_pages[-1]:
                break
            full_url = self.BASE_URL + relative_path

            try:
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "[async] get_book_chapter(%s page %d) failed: %s",
                    chapter_id,
                    idx,
                    exc,
                )
                break

            html_pages.append(html)
            idx += 1
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
    def relative_chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Return the relative URL path for a given chapter.
        """
        return f"/book/{book_id}/{chapter_id}.html"
