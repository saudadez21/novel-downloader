#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.uaa.fetcher
------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class UaaFetcher(GenericFetcher):
    """
    A session class for interacting with the 有爱爱 (www.uaa.com) novel.
    """

    site_name: str = "uaa"

    BOOK_INFO_URL = "https://www.uaa.com/novel/intro?id={book_id}"
    CHAPTER_URL = "https://www.uaa.com/novel/chapter?id={chapter_id}"
    BOOKCASE_URL = "https://www.uaa.com/member/collect"

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
            "FreeMarker template error",
            "Java stack trace",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
