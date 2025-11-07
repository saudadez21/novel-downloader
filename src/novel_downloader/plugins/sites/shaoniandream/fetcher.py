#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shaoniandream.fetcher
----------------------------------------------------
"""

import random
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ShaoniandreamFetcher(BaseFetcher):
    """
    A session class for interacting with the 少年梦 (www.shaoniandream.com) novel
    """

    site_name: str = "shaoniandream"

    BOOKCASE_URL = "https://www.shaoniandream.com/user/favobook"
    BOOK_INFO_URL = "https://www.shaoniandream.com/book_detail/{book_id}"
    BOOK_DETAIL_SIGN_UTL = "https://www.shaoniandream.com/booklibrary/getbookdetaildirsign/book_id/{book_id}"
    BOOK_DETAIL_URL = (
        "https://www.shaoniandream.com/booklibrary/getbookdetaildir/BookID/{book_id}"
    )
    CHAPTER_SIGN_URL = "https://www.shaoniandream.com/booklibrary/membersinglechaptersign/chapter_id/{chapter_id}"
    CHAPTER_URL = "https://www.shaoniandream.com/booklibrary/membersinglechapter/chapter_id/{chapter_id}"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [info, detail]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        info_html = await self.fetch(info_url, **kwargs)

        detail_url = self.BOOK_DETAIL_URL.format(book_id=book_id)
        params = {"randomm": self._get_rand()}
        headers = {
            **self.headers,
            "Origin": "https://www.shaoniandream.com",
            "Referer": f"https://www.shaoniandream.com/book_detail/{book_id}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        data = {
            "chapter_access_key": await self._get_book_detail_key(book_id),
        }

        resp = await self.session.post(
            detail_url, data=data, headers=headers, params=params, **kwargs
        )
        if not resp.ok:
            raise ConnectionError(
                f"esjzone book detail HTTP failed: {detail_url}, status={resp.status}"
            )

        detail_html = resp.text
        return [info_html, detail_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.CHAPTER_URL.format(chapter_id=chapter_id)
        params = {"randomm": self._get_rand()}
        headers = {
            **self.headers,
            "Origin": "https://www.shaoniandream.com",
            "Referer": f"https://www.shaoniandream.com/readchapter/{chapter_id}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        data = {
            "chapter_access_key": await self._get_chapter_key(chapter_id),
            "isMarket": "1",
        }

        resp = await self.session.post(
            url, data=data, headers=headers, params=params, **kwargs
        )
        if not resp.ok:
            raise ConnectionError(
                f"esjzone chapter HTTP failed: {url}, status={resp.status}"
            )

        return [resp.text]

    @staticmethod
    def _get_rand() -> str:
        return str(random.random())

    async def _get_book_detail_key(self, book_id: str) -> str:
        """
        Get the book's detail key used for unlocking chapters.
        """
        params = {"randoom": self._get_rand()}
        headers = {
            **self.headers,
            "Origin": "https://www.shaoniandream.com",
            "Referer": f"https://www.shaoniandream.com/book_detail/{book_id}",
            "X-Requested-With": "XMLHttpRequest",
        }
        url = self.BOOK_DETAIL_SIGN_UTL.format(book_id=book_id)

        resp = await self.session.post(url, params=params, headers=headers)
        if not resp.ok:
            self.logger.warning(
                "esjzone book detail key HTTP failed for %s, status=%s",
                url,
                resp.status,
            )
            return ""

        try:
            resp_json: dict[str, Any] = resp.json()
        except Exception as exc:
            self.logger.warning(
                "esjzone book detail key JSON parse failed for %s: %s", url, exc
            )
            return ""

        if (
            resp_json.get("status") == 1
            and isinstance(resp_json.get("data"), dict)
            and "chapter_access_key" in resp_json["data"]
        ):
            return str(resp_json["data"]["chapter_access_key"])

        raise ValueError(f"Unexpected book detail response: {resp_json}")

    async def _get_chapter_key(self, chapter_id: str) -> str:
        """
        Get the chapter access key for the given chapter id.
        """
        params = {"randoom": self._get_rand()}
        headers = {
            **self.headers,
            "Origin": "https://www.shaoniandream.com",
            "Referer": f"https://www.shaoniandream.com/readchapter/{chapter_id}",
            "X-Requested-With": "XMLHttpRequest",
        }
        url = self.CHAPTER_SIGN_URL.format(chapter_id=chapter_id)

        resp = await self.session.post(url, params=params, headers=headers)
        if not resp.ok:
            self.logger.warning(
                "esjzone chapter key HTTP failed for %s, status=%s", url, resp.status
            )
            return ""

        try:
            resp_json: dict[str, Any] = resp.json()
        except Exception as exc:
            self.logger.warning(
                "esjzone chapter key JSON parse failed for %s: %s", url, exc
            )
            return ""

        if (
            resp_json.get("status") == 1
            and isinstance(resp_json.get("data"), dict)
            and "chapter_access_key" in resp_json["data"]
        ):
            return str(resp_json["data"]["chapter_access_key"])

        raise ValueError(f"Unexpected chapter key response: {resp_json}")

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the user home page api content.

        :return: True if the user is logged in, False otherwise.
        """
        try:
            bookcase_html = await self.fetch(self.BOOKCASE_URL)
            keywords = {"验证码登录", "账号密码登录"}
            return not any(kw in bookcase_html for kw in keywords)
        except Exception as e:
            self.logger.info("shaoniandream login check failed: %s", e)
        return False
