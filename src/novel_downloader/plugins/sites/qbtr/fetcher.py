#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qbtr.fetcher
-------------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class QbtrSession(BaseSession):
    """
    A session class for interacting with the 全本同人小说 (www.qbtr.cc) novel.
    """

    site_name: str = "qbtr"

    BASE_URL = "https://www.qbtr.cc"
    BOOK_INFO_URL = "https://www.qbtr.cc/{book_id}.html"
    CHAPTER_URL = "https://www.qbtr.cc/{book_id}/{chapter_id}.html"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [info, download]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        book_id = book_id.replace("-", "/")
        url = self.book_info_url(book_id=book_id)
        info_html = await self.fetch(url, **kwargs)
        try:
            info_tree = html.fromstring(info_html)
            txt_link = info_tree.xpath(
                '//div[@class="booktips"]/h3/a[contains(text(), "txt下载")]/@href'
            )
            download_url = f"{self.BASE_URL}{txt_link[0]}" if txt_link else None
        except Exception:
            download_url = None

        download_html = await self.fetch(download_url, **kwargs) if download_url else ""
        return [info_html, download_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

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
