#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sfacg.fetcher
--------------------------------------------

"""

import base64
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class SfacgFetcher(BaseFetcher):
    """
    A session class for interacting with the SF轻小说 (m.sfacg.com) novel.
    """

    site_name: str = "sfacg"

    LOGIN_URL = "https://m.sfacg.com/login"
    BOOKCASE_URL = "https://m.sfacg.com/sheets/"
    BOOK_INFO_URL = "https://m.sfacg.com/b/{book_id}/"
    BOOK_CATALOG_URL = "https://m.sfacg.com/i/{book_id}/"
    CHAPTER_URL = "https://m.sfacg.com/c/{chapter_id}/"
    VIP_CHAPTER_URL = "https://m.sfacg.com/ajax/ashx/common.ashx"

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
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        info_html = await self.fetch(info_url, **kwargs)
        catalog_html = await self.fetch(catalog_url, **kwargs)

        return [info_html, catalog_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        raw_html = await self.fetch(url, **kwargs)

        results: list[str] = [raw_html]

        # If the chapter contains VIP image content
        if "/ajax/ashx/common.ashx" in raw_html:
            params = {
                "op": "getChapPic",
                "cid": chapter_id,
                "nid": book_id,
                "w": "375",
                "font": "20",
                "quick": "true",
            }
            resp = await self.session.get(self.VIP_CHAPTER_URL, params=params)
            if not resp.ok:
                raise ConnectionError(
                    f"VIP chapter image request failed: {self.VIP_CHAPTER_URL}, status={resp.status}"  # noqa: E501
                )

            img_base64 = base64.b64encode(resp.content).decode("utf-8")
            results.append(img_base64)

        return results

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

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
        return cls.CHAPTER_URL.format(chapter_id=chapter_id)

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "请输入用户名和密码",
            "用户未登录",
            "可输入用户名",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
