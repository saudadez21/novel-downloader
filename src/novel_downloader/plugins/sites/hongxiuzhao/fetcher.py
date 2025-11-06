#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hongxiuzhao.fetcher
--------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class HongxiuzhaoFetcher(GenericFetcher):
    """
    A session class for interacting with the 红袖招 (hongxiuzhao.net) novel
    """

    site_name: str = "hongxiuzhao"

    BASE_URL = "https://hongxiuzhao.net"
    BOOK_INFO_URL = "https://hongxiuzhao.net/{book_id}.html"
    BOOKCASE_URL = "https://www.ciyuanji.com/user/rack.html"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return f"/{chapter_id}.html" if idx == 1 else f"/{chapter_id}_{idx}.html"

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            # "请输入账号",
            # "请输入密码",
            "Enable JavaScript and cookies to continue",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
